from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtCore import Qt, QRectF, QPointF

import config
from config import GRID_SIZE, PanelMode, Tool


class Tile(QGraphicsItem):
    property_specs = []

    def __init__(self):
        super().__init__()
        self.selected = False
        self.setTransformOriginPoint(GRID_SIZE / 2, GRID_SIZE / 2)

        for spec in self.property_specs:
            setattr(self, spec["key"], spec["default"])

    def boundingRect(self):
        return QRectF(0, 0, GRID_SIZE, GRID_SIZE)

    def edge_point(self, direction):
        s = GRID_SIZE
        points = {
            "N": (s / 2, 0),
            "S": (s / 2, s),
            "E": (s, s / 2),
            "W": (0, s / 2),
            "NE": (s, 0),
            "NW": (0, 0),
            "SE": (s, s),
            "SW": (0, s),
            "C": (s / 2, s / 2),
        }
        return QPointF(*points[direction])

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipRect(self.boundingRect())
        self.draw(painter)
        if self.selected:
            self._draw_selection_highlight(painter)

    def draw(self, painter):
        raise NotImplementedError("Subclasses must implement draw()")

    def draw_tile_background(self, painter):
        painter.setBrush(QBrush(QColor(config.TILE_COLOR)))
        pen =QPen(QColor(config.TILE_BORDER_COLOR))
        pen.setWidth(config.TILE_BORDER_WIDTH)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

    def _draw_selection_highlight(self, painter):
        pen = QPen(QColor(config.SELECTION_HIGHLIGHT_COLOR))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.boundingRect())

    def draw_line(self, painter, start, end, active):
        color = QColor(config.TRACK_COLOR) if active else QColor(config.INACTIVE_TRACK_COLOR)    
        pen = QPen(color)
        pen.setWidth(config.TRACK_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.edge_point(start), self.edge_point(end))

    def rotate_cw(self):
        self.setRotation((self.rotation() + 90) % 360)

    def mousePressEvent(self, event):
        scene = self.scene()
        if scene is None:
            return

        if scene.mode == PanelMode.OPERATE:
            self.on_tap()
            self.update()
            return

        # Edit mode
        if scene.tool == Tool.SELECT:
            scene.select_tile(self)
        elif scene.tool == Tool.PLACE:
            pass # tappping an occupied tile while pacing: no-op
        elif scene.tool == Tool.MOVE:
            pass # moving torgets empty cells only; handled at scene level

    def on_tap(self):
        raise NotImplementedError("Subclass must be implement on_tap()")    

    def to_dict(self):
        data = {
            "type": self.__class__.__name__,
            "rotation": self.rotation(),
        }
        for spec in self.property_specs:
            data[spec["key"]] = getattr(self, spec["key"])
        return data 

    @classmethod
    def from_dict(cls, data):
        tile = cls()
        tile.setRotation(data["rotation"])
        for spec in cls.property_specs:
            tile_value = data.get(spec["key"], spec["default"])
            setattr(tile, spec["key"], tile_value)
        return tile


            