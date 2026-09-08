from PySide6.QtGui import QColor, QPen
from PySide6.QtCore import Qt

from tile import Tile
import config

class Straight(Tile):
    def __init__(self):
        super().__init__()

    def on_tap(self):
        pass

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

    def on_tap(self):
        pass

    def draw(self, painter):
        self.draw_tile_background(painter)

        pen = QPen(QColor(config.TRACK_COLOR))
        pen.setWidth(config.TRACK_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.edge_point("W"), self.edge_point("S"))