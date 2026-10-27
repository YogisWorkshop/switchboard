import sys

from PySide6.QtCore import QCoreApplication, QTimer

from stations.fake import FakeBridge

app = QCoreApplication(sys.argv)

bridge = FakeBridge()
bridge.RETRY_MS = 1000
bridge.state_changed.connect(lambda s: print(f"  state: {s.name}"))
bridge.turnout_changed.connect(
    lambda a, p, d: print(f"  confirmed: turnout {a} {p} {'diverging' if d else 'straight'}")
)


def try_send(label):
    print(f"{label}: send accepted = {bridge.send_turnout(5, 'DCC', True)}")


def lose():
    print("pull the cable")
    bridge.simulate_loss()


steps = [
    (0,    bridge.start),
    (500,  lambda: try_send("while connecting")),
    (2000, lambda: try_send("while connected")),
    (3000, lose),
    (3200, lambda: try_send("while lost")),
    (7000, lambda: try_send("after reconnect")),
    (8000, bridge.stop),
    (8200, lambda: try_send("after stop")),
    (9000, app.quit),
]
for delay, action in steps:
    QTimer.singleShot(delay, action)

app.exec()
