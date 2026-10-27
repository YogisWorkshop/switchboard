import threading
from enum import Enum, auto

from PySide6.QtCore import QObject, QTimer, Signal


class ConnectionState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    LOST = auto()


class StationBridge(QObject):
    state_changed = Signal(object)
    turnout_changed = Signal(int, str, bool)
    power_changed = Signal(object)                # True = GO, False = STOP, None = unknown

    _connect_finished = Signal(object)
    _power_reported = Signal(object)
    _lost = Signal()

    RETRY_MS = 5000

    def __init__(self):
        super().__init__()
        self.state = ConnectionState.DISCONNECTED
        self._wanted = False
        self._connecting = False
        self.power = None             # True = GO, False = STOP, None = unknown

        self._retry_timer = QTimer(self)
        self._retry_timer.setSingleShot(True)
        self._retry_timer.timeout.connect(self._try_connect)

        self._connect_finished.connect(self._on_connect_finished)
        self._lost.connect(self._on_lost)
        self._power_reported.connect(self._set_power)

    def start(self):
        self._wanted = True
        self._try_connect()

    def stop(self):
        self._wanted = False
        self._retry_timer.stop()
        self._close()
        self._set_state(ConnectionState.DISCONNECTED)

    def send_turnout(self, address, protocol, diverging):
        if self.state != ConnectionState.CONNECTED:
            return False
        try:
            self._send_turnout(address, protocol, diverging)
        except OSError:
            self.report_lost()
            return False
        except ValueError as error:           # e.g. an address the station can't use
            print(f"Cannot send: {error}")
            return False
        return True

    def send_power(self, on):
        """Track power: True = GO, False = STOP. Returns True if handed to the station."""
        if self.state != ConnectionState.CONNECTED:
            return False
        try:
            self._send_power(on)
        except OSError:
            self.report_lost()
            return False
        return True

    def report_lost(self):
        self._lost.emit()

    def report_power(self, on):
        self._power_reported.emit(on)

    def _open(self):
        raise NotImplementedError

    def _close(self):
        raise NotImplementedError

    def _send_turnout(self, address, protocol, diverging):
        raise NotImplementedError

    def _send_power(self, on):
        raise NotImplementedError

    def _resync(self):
        pass

    def _set_state(self, state):
        if state != self.state:
            self.state = state
            self.state_changed.emit(state)
        if state != ConnectionState.CONNECTED:
            self._set_power(None)                 # no connection, no idea

    def _set_power(self, on):
        if on != self.power:
            self.power = on
            self.power_changed.emit(on)

    def _try_connect(self):
        if self._connecting or self.state == ConnectionState.CONNECTED:
            return
        self._connecting = True
        if self.state != ConnectionState.LOST:
            self._set_state(ConnectionState.CONNECTING)

        def work():
            try:
                self._open()
                self._resync()
            except Exception as error:
                self._connect_finished.emit(error)
            else:
                self._connect_finished.emit(None)

        threading.Thread(target=work, daemon=True).start()

    def _on_connect_finished(self, error):
        self._connecting = False
        if not self._wanted:
            self._close()
            return
        if error is not None:
            self._close()
            self._set_state(ConnectionState.LOST)
            self._retry_timer.start(self.RETRY_MS)
            return
        self._set_state(ConnectionState.CONNECTED)

    def _on_lost(self):
        if self.state == ConnectionState.DISCONNECTED:
            return
        self._close()
        self._set_state(ConnectionState.LOST)
        if self._wanted:
            self._retry_timer.start(self.RETRY_MS)