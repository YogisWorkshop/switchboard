import config
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtCore import Qt, QRectF, QPointF
from tile import Tile

class TurnoutRight(Tile):
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""}, 
        {"key": "address", "label": "Address", "type": int, "default": 0},
        {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"}
        ]

    def __init__(self):
        super().__init__()
        self.thrown = False

    def on_tap(self):
         self.thrown = not self.thrown

    def draw(self, painter):
        self.draw_tile_background(painter)

        if self.thrown:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", "S", active=True)
        else:
            self.draw_line(painter, "W", "S", active=False)
            self.draw_line(painter, "W", "E", active=True)


class TurnoutLeft(Tile):
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""}, 
        {"key": "address", "label": "Address", "type": int, "default": 0},
        {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"}
        ]

    def __init__(self):
        super().__init__()
        self.thrown = False

    def on_tap(self):
         self.thrown = not self.thrown

    def draw(self, painter):
        self.draw_tile_background(painter)

        if self.thrown:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", "N", active=True)
        else:
            self.draw_line(painter, "W", "N", active=False)
            self.draw_line(painter, "W", "E", active=True)


class Turnout3Way(Tile):
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""}, 
        {"key": "address", "label": "Address", "type": int, "default": 0},
        {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"}
        ]
    
    def __init__(self):
        super().__init__()
        self._pattern = [0, 1, 0, 2]
        self._index = 0
        self.thrown_state = 0

    def on_tap(self):
        self._index = (self._index + 1) % 4
        self.thrown_state = self._pattern[self._index]
        
    def draw(self, painter):
        self.draw_tile_background(painter)

        if self.thrown_state == 1:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", "S", active=False)
            self.draw_line(painter, "W", "N", active=True)
        elif self.thrown_state == 2:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", "N", active=False)
            self.draw_line(painter, "W", "S", active=True)
        else:
            self.draw_line(painter, "W", "N", active=False)
            self.draw_line(painter, "W", "S", active=False)
            self.draw_line(painter, "W", "E", active=True)


class Signal(Tile):
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""}, 
        {"key": "address", "label": "Address", "type": int, "default": 0},
        {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"}
        ]

    def __init__(self):
        super().__init__()
        self.show_red = False

    def on_tap(self):
         self.show_red = not self.show_red

    def draw(self, painter):
        self.draw_tile_background(painter)

        pen = QPen(QColor(config.TRACK_COLOR))
        pen.setWidth(config.TRACK_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.drawLine(self.edge_point("W"), self.edge_point("E"))

        signal_head_pos_y = ((config.GRID_SIZE * 0.75) + (config.TRACK_WIDTH / 4)) / 80
        signal_head_bottom = self.point_at(0.7, signal_head_pos_y)
        signal_head_top = self.point_at(0.4, signal_head_pos_y)
        width = config.TRACK_WIDTH * 1.5
        self.draw_signal_element(painter, signal_head_bottom, signal_head_top, width)



        if self.show_red:
            painter.setBrush(QBrush("#ff3333"))
            painter.setPen(Qt.PenStyle.NoPen)
            center = self.point_at(0.5, signal_head_pos_y)
            radius = config.TRACK_WIDTH / 2
            painter.drawEllipse(center, radius, radius)
        else:
            painter.setBrush(QBrush("#33cc33"))
            painter.setPen(Qt.PenStyle.NoPen)
            center = self.point_at(0.7, signal_head_pos_y)
            radius = config.TRACK_WIDTH / 2
            painter.drawEllipse(center, radius, radius)
  
    


     
