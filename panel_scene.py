from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Signal

from tile_registry import TILE_CLASSES
import config
from config import (TILE_BORDER_WIDTH,
                     PanelMode, Tool)

class PanelScene(QGraphicsScene):
    selection_changed = Signal(object)

    def __init__(self, grid_size):
        super().__init__()
        self.grid_size = grid_size

        self.mode = PanelMode.EDIT
        self.tool = Tool.SELECT
        self.armed_tile_type = None
        self.selected_tile = None

        self.tiles_by_cell = {}

    def drawBackground(self, painter, rect):
        scene_rect = self.sceneRect()
        draw_rect = rect.intersected(scene_rect)

        painter.fillRect(draw_rect, QColor(config.BACKGROUND_COLOR))

        pen = QPen(QColor(config.TILE_BORDER_COLOR))
        pen.setWidth(TILE_BORDER_WIDTH)
        painter.setPen(pen)

        left = int(draw_rect.left()) - (int(draw_rect.left()) % self.grid_size)
        top = int(draw_rect.top()) - (int(draw_rect.top()) % self.grid_size)

        x = left
        while x < draw_rect.right():
            painter.drawLine(x, draw_rect.top(), x, draw_rect.bottom())
            x += self.grid_size

        y = top
        while y < draw_rect.bottom():
            painter.drawLine(draw_rect.left(), y, draw_rect.right(), y)
            y += self.grid_size

    def mousePressEvent(self, event):
        if self.mode != PanelMode.EDIT:
            super().mousePressEvent(event)
            return

        pos = event.scenePos()
        col = int(pos.x()) // self.grid_size
        row = int(pos.y()) // self.grid_size

        if self.tool == Tool.PLACE:
            if (col, row) in self.tiles_by_cell:
                print(f"Cell ({col}, {row}) is already occupied")
                return
            tile = self.armed_tile_type()
            tile.setPos(col * self.grid_size, row * self.grid_size)
            self.addItem(tile)
            self.tiles_by_cell[(col, row)] = tile
            return

        if self.tool == Tool.MOVE:
            if (col, row) in self.tiles_by_cell:
                print(f"Cell ({col}, {row}) is already occupied")
                return
            self.move_tile(self.selected_tile, col, row)
            return

        # Tool.SELECT and tap landed on empty space
        self.clear_selection()
        super().mousePressEvent(event)

    def cell_for_tile(self, tile):
        col = int(tile.x()) // self.grid_size
        row = int(tile.y()) // self.grid_size
        return col, row

    def select_tile(self, tile):
        if self.selected_tile is not None:
            self.selected_tile.selected = False
            self.selected_tile.update()

        self.selected_tile = tile
        tile.selected = True
        tile.update()
        self.selection_changed.emit(tile)

    def clear_selection(self):
        if self.selected_tile is not None:
            self.selected_tile.selected = False
            self.selected_tile.update()
        self.selected_tile = None
        self.selection_changed.emit(None)

    def remove_tile(self, tile):
        cell = self.cell_for_tile(tile)
        self.tiles_by_cell.pop(cell, None)
        self.removeItem(tile)
        if self.selected_tile is tile:
            self.selected_tile = None
            self.selection_changed.emit(None)

    def move_tile(self, tile, col, row):
        old_cell = self.cell_for_tile(tile)
        self.tiles_by_cell.pop(old_cell, None)
        tile.setPos(col * self.grid_size, row * self.grid_size)
        self.tiles_by_cell[(col, row)] = tile

    def open_properties(self, tile):
        print(f"Open properties for {tile.__class__.__name__} (not yet implemented)")

    def save_to_dict(self):
        tiles_data = []
        for (col, row), tile in self.tiles_by_cell.items():
            data = tile.to_dict()
            data["col"] = col
            data["row"] = row
            tiles_data.append(data)

        return {
            "grid_size": self.grid_size,
            "tiles": tiles_data,
        }

    def load_from_dict(self, layout_data):
        self.clear_selection()
        for tile in list(self.tiles_by_cell.values()):
            self.removeItem(tile)
        self.tiles_by_cell.clear()

        for tile_data in layout_data.get("tiles", []):
            tile_class = TILE_CLASSES[tile_data["type"]]
            tile = tile_class.from_dict(tile_data)

            col = tile_data["col"]
            row = tile_data["row"]
            tile.setPos(col * self.grid_size, row * self.grid_size)

            self.addItem(tile)
            self.tiles_by_cell[(col, row)] = tile
            