from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtCore import Qt, QRectF, QPointF

import config
from config import PanelMode, Tool


class Tile(QGraphicsItem):
    property_specs = []

    def __init__(self):
        super().__init__()
        self.selected = False
        self.setTransformOriginPoint(config.GRID_SIZE / 2, config.GRID_SIZE / 2)

        for spec in self.property_specs:
            setattr(self, spec["key"], spec["default"])

    def boundingRect(self):
        return QRectF(0, 0, config.GRID_SIZE, config.GRID_SIZE)

    def edge_point(self, direction):
        s = config.GRID_SIZE
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

    def point_at(self, fx, fy):
        return QPointF(fx * config.GRID_SIZE, fy * config.GRID_SIZE)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipRect(self.boundingRect())
        self.draw(painter)
        if self.selected:
            self._draw_selection_highlight(painter)

    def draw(self, painter):
        pass

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

    def draw_segment(self, painter, start_point, end_point):
        pen = QPen(QColor(config.TRACK_COLOR))
        pen.setWidth(config.TRACK_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.drawLine(start_point, end_point)

    def draw_signal_element(self, painter, start_point, end_point, width):
            pen = QPen(QColor(config.TRACK_COLOR))
            pen.setWidth(width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(start_point, end_point)

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

    def mouseReleaseEvent(self, event):
        scene = self.scene()
        if scene is None:
            return
        if scene.mode == PanelMode.OPERATE:
            self.on_release()
            self.update()

    def on_release(self):
        pass

    def on_tap(self):
        pass    

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

class Empty(Tile):
    def __init__(self):
        super().__init__()

    def on_tap(self):
        pass
    
    def draw(self, painter):
        self.draw_tile_background(painter)

class Button(Tile):
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
        self.on_state = False

    def on_tap(self):
        if self.mode == "Momentary":
            self.on_state = True
        else:
            self.on_state = not self.on_state

    def on_release(self):
        if self.mode == "Momentary":
            self.on_state = False

    def draw(self, painter):
        self.draw_tile_background(painter)

        on_color, off_color = self._colors_for(self.color)
        fill_color = QColor(on_color) if self.on_state else QColor(off_color)

        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.PenStyle.NoPen)
        center = self.point_at(0.5, 0.5)
        radius = config.GRID_SIZE * 0.25
        painter.drawEllipse(center, radius, radius)    

    def _colors_for(self, color_name):
        mapping = {
            "Red": (config.BUTTON_COLOR_RED_ON, config.BUTTON_COLOR_RED_OFF),
            "Green": (config.BUTTON_COLOR_GREEN_ON, config.BUTTON_COLOR_GREEN_OFF),
            "Blue": (config.BUTTON_COLOR_BLUE_ON, config.BUTTON_COLOR_BLUE_OFF),
        }
        return mapping[color_name]