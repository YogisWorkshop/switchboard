"""ECoS client: a background thread reads, the main program sends."""

import queue
import threading

from stations.ecos import connection


class EcosClient:
    def __init__(self, host, on_event, on_disconnect):
        self.on_event = on_event
        self.on_disconnect = on_disconnect
        self.replies = queue.Queue()
        self.send_lock = threading.Lock()
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
        with self.send_lock:               # one command at a time: replies carry no id
            while not self.replies.empty():    # drop a late reply from an earlier timeout
                self.replies.get_nowait()
            self.connection.send(command)
            try:
                return self.replies.get(timeout=3)
            except queue.Empty:
                raise TimeoutError(f"no reply to {command!r}") from None

    def close(self):
        self.connection.close()
        self.reader.join(timeout=1)