"""ECoS client: a background thread reads, the main program sends."""

import queue
import threading

import connection


class EcosClient:
    def __init__(self, host, on_event, on_disconnect):
        self.on_event = on_event
        self.on_disconnect = on_disconnect
        self.replies = queue.Queue()
        self.connection = connection.Connection(host)
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()

    def _read_loop(self):
        try:
            while True:
                try:
                    message = self.connection.read_message()
                except TimeoutError:
                    continue
                if message.kind == "REPLY":
                    self.replies.put(message)
                else:
                    self.on_event(message)
        except OSError:
            pass
        self.on_disconnect()

    def send_command(self, command):
        self.connection.send(command)
        try:
            return self.replies.get(timeout=3)
        except queue.Empty:
            raise TimeoutError(f"no reply to {command!r}") from None

    def close(self):
        self.connection.close()
        self.reader.join(timeout=1)