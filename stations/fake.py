import time

from PySide6.QtCore import QTimer

from stations.bridge import StationBridge


class FakeBridge(StationBridge):
    """Pretends to be a station, so we can test without hardware."""

    def __init__(self):
        super().__init__()
        self.fail_connects = False

    def _open(self):
        time.sleep(1.0)                    # a real connect takes time
        if self.fail_connects:
            raise ConnectionError("fake station unreachable")

    def _resync(self):
        self.report_power(False)           # starts out stopped

    def _close(self):
        pass

    def _send_turnout(self, address, protocol, diverging):
        # a real station confirms a moment later
        QTimer.singleShot(
            150, lambda: self.turnout_changed.emit(address, protocol, diverging)
        )

    def _send_power(self, on):
        QTimer.singleShot(150, lambda: self.report_power(on))

    def simulate_loss(self):
        self.report_lost()