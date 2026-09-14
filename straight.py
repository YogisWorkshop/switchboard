from PySide6.QtGui import QColor, QPen, QBrush
from PySide6.QtCore import Qt

from tile import Tile, Button
import config

class Straight(Tile):
    def __init__(self):
        super().__init__()

    def draw(self, painter):
        self.draw_tile_background(painter)

        pen = QPen(QColor(config.TRACK_COLOR))
        pen.setWidth(config.TRACK_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.drawLine(self.edge_point("W"), self.edge_point("E"))

class Diagonal(Tile):
    def __init__(self):
        super().__init__()

    def draw(self, painter):
        self.draw_tile_background(painter)

        pen = QPen(QColor(config.TRACK_COLOR))
        pen.setWidth(config.TRACK_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.edge_point("W"), self.edge_point("S"))

class DiagonalDouble(Tile):
    def __init__(self):
        super().__init__()

    def draw(self, painter):
        self.draw_tile_background(painter)

        pen = QPen(QColor(config.TRACK_COLOR))
        pen.setWidth(config.TRACK_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.edge_point("W"), self.edge_point("S"))
        painter.drawLine(self.edge_point("N"), self.edge_point("E"))


class StraightBumper(Tile):

    def __init__(self):
        super().__init__()

    def draw(self, painter):
        self.draw_tile_background(painter)

        track_segment_start = self.point_at(0, 0.5)
        track_segment_stop = self.point_at(0.6, 0.5)
        self.draw_segment(painter, track_segment_start, track_segment_stop)

        crossbar_half_lenght = 0.2
        top = self.point_at(0.6, 0.5 - crossbar_half_lenght)
        bottom = self.point_at(0.6, 0.5 + crossbar_half_lenght)
        self.draw_segment(painter, top, bottom)

class TrackButton(Button):
    property_specs = [
                {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
                {"key": "name", "label": "Name", "type": str, "default": ""}, 
                {"key": "address", "label": "Address", "type": int, "default": 0},
                {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"},
                {"key": "color", "label": "Color", "type": "choice", "choices": ["Red", "Green", "Blue"], "default": "Blue"},
                {"key": "mode", "label": "Mode", "type": "choice", "choices": ["Toggle", "Momentary"], "default": "Toggle"},
                ]
    
    def __init__(self):
        super().__init__()

    def draw(self, painter):
        self.draw_tile_background(painter)
        self. draw_line(painter, "W", "E", active=True)
    
        on_color, off_color = self._colors_for(self.color)
        fill_color = QColor(on_color) if self.on_state else QColor(off_color)
    
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.PenStyle.NoPen)
        center = self.point_at(0.5, 0.5)
        radius = config.GRID_SIZE * 0.25
        painter.drawEllipse(center, radius, radius)
