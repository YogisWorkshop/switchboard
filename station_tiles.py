from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import Qt, QRectF, QPointF

import config
from tile import Tile
from stations.bridge import ConnectionState


class StationTile(Tile):
    """Base for tiles that show or control the station itself."""
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""},
    ]

    def _bridge(self):
        scene = self.scene()
        return scene.bridge if scene is not None else None


class ConnectionTile(StationTile):
    """Shows the station connection. Tap to connect, long-press to disconnect."""

    def _state_color(self):
        bridge = self._bridge()
        if bridge is None:
            return config.CONNECTION_COLOR_OFF
        colors = {
            ConnectionState.CONNECTED: config.CONNECTION_COLOR_CONNECTED,
            ConnectionState.CONNECTING: config.CONNECTION_COLOR_CONNECTING,
            ConnectionState.LOST: config.CONNECTION_COLOR_LOST,
        }
        return colors.get(bridge.state, config.CONNECTION_COLOR_OFF)

    def on_tap(self):
        bridge = self._bridge()
        if bridge is None:
            return
        if bridge.state in (ConnectionState.DISCONNECTED, ConnectionState.LOST):
            bridge.start()
        else:
            # connected or connecting: only a long press does anything
            self.start_long_press(self._long_press)

    def _long_press(self):
        self._press_timer = None
        bridge = self._bridge()
        if bridge is None:
            return
        self.ungrabMouse()      # the dialog will swallow the release event
        if bridge.state == ConnectionState.CONNECTED:
            answer = QMessageBox.question(
                QApplication.activeWindow(),
                "Disconnect",
                f"Disconnect from {config.STATION_TYPE}?\n\n"
                "Depending on the station's settings, trains may stop.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        bridge.stop()

    def _shows_cross(self):
        """The X: not connected on purpose, or no station chosen at all."""
        bridge = self._bridge()
        return bridge is None or bridge.state == ConnectionState.DISCONNECTED

    def draw(self, painter):
        self.draw_tile_background(painter)

        size = config.GRID_SIZE
        center = self.point_at(0.5, 0.5)
        ring_radius = size * 0.25
        ring_width = min(max(3, config.TRACK_WIDTH * 0.75), size * 0.1)

        # track stubs from the tile edges to the ring
        self.draw_segment(painter, self.edge_point("W"), self.point_at(0.5 - 0.25, 0.5))
        self.draw_segment(painter, self.point_at(0.5 + 0.25, 0.5), self.edge_point("E"))

        # the ring: two arcs, with a small gap top right and bottom left
        pen = QPen(QColor(config.TRACK_COLOR))
        pen.setWidth(int(ring_width))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        box = QRectF(center.x() - ring_radius, center.y() - ring_radius,
                     ring_radius * 2, ring_radius * 2)
        gap = 32                                  # degrees, centred on 65 and 245
        span = 180 - gap
        painter.drawArc(box, int((65 + gap / 2) * 16), int(span * 16))
        painter.drawArc(box, int((245 + gap / 2) * 16), int(span * 16))

        # the state: a colored dot
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(self._state_color())))
        dot_radius = size * 0.20
        painter.drawEllipse(center, dot_radius, dot_radius)

        # not connected: an X over the dot
        if self._shows_cross():
            pen = QPen(QColor(config.TRACK_COLOR))
            pen.setWidth(max(3, int(config.TRACK_WIDTH / 3)))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            d = size * 0.11
            painter.drawLine(QPointF(center.x() - d, center.y() - d),
                             QPointF(center.x() + d, center.y() + d))
            painter.drawLine(QPointF(center.x() - d, center.y() + d),
                             QPointF(center.x() + d, center.y() - d))


class PowerTile(StationTile):
    """Track power. Tap = STOP. Long-press = GO."""

    def _power_color(self):
        bridge = self._bridge()
        if bridge is None or bridge.power is None:
            return config.POWER_COLOR_UNKNOWN
        return config.POWER_COLOR_GO if bridge.power else config.POWER_COLOR_STOP

    def on_tap(self):
        bridge = self._bridge()
        if bridge is None or bridge.state != ConnectionState.CONNECTED:
            return
        if bridge.power is False:
            # stopped: starting takes a long press
            self.start_long_press(self._go)
        else:
            # running, or not known: stopping is always one tap
            bridge.send_power(False)

    def _go(self):
        self._press_timer = None
        bridge = self._bridge()
        if bridge is not None and bridge.power is False:
            bridge.send_power(True)

    def draw(self, painter):
        self.draw_tile_background(painter)

        pen = QPen(QColor(self._power_color()))
        pen.setWidth(max(4, config.TRACK_WIDTH // 2))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # the classic power symbol: a ring open at the top, with a bar in the gap
        size = config.GRID_SIZE * 0.5
        left = (config.GRID_SIZE - size) / 2
        painter.drawArc(int(left), int(left + size * 0.1), int(size), int(size),
                        125 * 16, 290 * 16)
        painter.drawLine(self.point_at(0.5, 0.2), self.point_at(0.5, 0.5))