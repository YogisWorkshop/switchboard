import math

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPen, QPolygonF
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
    """Track power. Tap = STOP. Long-press = GO.

    Symbol and Round show the STATE of the power. Stop sign shows the ACTION
    a press will do right now.
    """
    property_specs = StationTile.property_specs + [
        {"key": "style", "label": "Style", "type": "choice",
         "choices": ["Symbol", "Round", "Stop sign"], "default": "Symbol"},
    ]

    # ---- behavior -------------------------------------------------------

    def _action(self):
        """What a press does right now: "STOP", "GO", or None (nothing)."""
        bridge = self._bridge()
        if bridge is None or bridge.state != ConnectionState.CONNECTED:
            return None
        # stopped: starting takes a long press. Running, or not known: one tap stops.
        return "GO" if bridge.power is False else "STOP"

    def on_tap(self):
        action = self._action()
        if action == "GO":
            self.start_long_press(self._go)
        elif action == "STOP":
            self._bridge().send_power(False)

    def _go(self):
        self._press_timer = None
        if self._action() == "GO":
            self._bridge().send_power(True)

    # ---- drawing --------------------------------------------------------

    def _state_color(self):
        bridge = self._bridge()
        if bridge is None or bridge.power is None:
            return config.POWER_COLOR_UNKNOWN
        return config.POWER_COLOR_GO if bridge.power else config.POWER_COLOR_STOP

    def _action_color(self):
        return {"STOP": config.POWER_COLOR_STOP,
                "GO": config.POWER_COLOR_GO}.get(self._action(), config.POWER_COLOR_UNKNOWN)

    def draw(self, painter):
        self.draw_tile_background(painter)
        if self.style == "Round":
            self._draw_round(painter)
        elif self.style == "Stop sign":
            self._draw_stop_sign(painter)
        else:
            self._draw_symbol(painter)

    def _draw_symbol(self, painter):
        pen = QPen(QColor(self._state_color()))
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

    def _draw_round(self, painter):
        """An indicator lamp: no text, so it reads as a display, not a button."""
        pen = QPen(QColor(config.TRACK_COLOR))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(self._state_color())))
        radius = config.GRID_SIZE * 0.30
        painter.drawEllipse(self.point_at(0.5, 0.5), radius, radius)

    def _octagon(self, radius):
        center = self.point_at(0.5, 0.5)
        points = []
        for k in range(8):
            angle = math.radians(22.5 + 45 * k)      # flat top and bottom, like the sign
            points.append(QPointF(center.x() + radius * math.cos(angle),
                                  center.y() + radius * math.sin(angle)))
        return QPolygonF(points)

    def _draw_stop_sign(self, painter):
        """Shows what pressing does: STOP when you can stop, GO when you can start."""
        action = self._action()
        color = QColor(self._action_color())
        text_color = QColor("white") if action != "GO" else QColor(config.TRACK_COLOR)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(self._octagon(config.GRID_SIZE * 0.44))

        border = QPen(QColor("white") if action is not None else QColor(config.TILE_COLOR))
        border.setWidth(max(2, config.GRID_SIZE // 30))
        painter.setPen(border)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(self._octagon(config.GRID_SIZE * 0.38))

        text = action or "STOP"
        font = QFont()
        font.setBold(True)
        pixel_size = int(config.GRID_SIZE * 0.22)
        font.setPixelSize(pixel_size)
        while pixel_size > 6 and QFontMetrics(font).horizontalAdvance(text) > config.GRID_SIZE * 0.58:
            pixel_size -= 1                          # shrink until it fits inside the sign
            font.setPixelSize(pixel_size)
        painter.setFont(font)
        painter.setPen(text_color if action is not None else QColor(config.TILE_COLOR))
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, text)