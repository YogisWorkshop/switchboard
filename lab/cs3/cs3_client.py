"""CS3 client: a background thread reads frames, the main program sends.

Same shape as EcosClient. The CS3 has no request/reply pairing like the
ECoS; instead it mirrors traffic with the response bit set. request() sends
a frame and waits for the first response frame with the same command and
the same first four data bytes (the target UID).
"""

import queue
import socket
import threading

import cs3_protocol


class Cs3Client:
    def __init__(self, host, on_frame, on_disconnect, port=cs3_protocol.CS3_PORT):
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect
        self.replies = queue.Queue()
        self.expected = None               # the frame request() is waiting on
        self.framer = cs3_protocol.Framer()
        self.sock = socket.create_connection((host, port), timeout=3)
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()

    def _read_loop(self):
        try:
            while True:
                try:
                    data = self.sock.recv(1024)
                except socket.timeout:     # = TimeoutError on Python 3.10+, older too
                    continue
                if not data:
                    break                  # CS3 closed the connection
                for frame in self.framer.feed(data):
                    if self._is_expected_reply(frame):
                        self.replies.put(frame)
                    self.on_frame(frame)
        except OSError:
            pass
        self.on_disconnect()

    def _is_expected_reply(self, frame):
        expected = self.expected
        return (expected is not None
                and frame.response
                and frame.command == expected.command
                and frame.data[:4] == expected.data[:4])

    def send(self, frame):
        """Send without waiting for anything."""
        self.sock.sendall(frame.to_bytes())

    def request(self, frame, timeout=1.0):
        """Send, then wait for the matching response. Returns it, or None."""
        while not self.replies.empty():    # throw away late replies from before
            self.replies.get_nowait()
        self.expected = frame
        try:
            self.send(frame)
            return self.replies.get(timeout=timeout)
        except queue.Empty:
            return None
        finally:
            self.expected = None

    def switch_accessory(self, address, position, protocol="DCC", switch_time=10):
        """One frame, CS3 times the coil (same method as the club bridge).

        Returns the CS3's confirmation frame, or None.
        """
        frame = cs3_protocol.accessory_frame(address, position, 1, protocol, switch_time)
        return self.request(frame)

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()
        self.reader.join(timeout=1)
