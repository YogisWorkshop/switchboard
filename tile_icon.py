from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtCore import Qt

import config
from config import GRID_SIZE

def render_tile_icon(tile_instance, size=GRID_SIZE):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    original_inactive_color = config.INACTIVE_TRACK_COLOR
    config.INACTIVE_TRACK_COLOR = config.TRACK_COLOR
    try:
        tile_instance.draw(painter)
    finally:
        config.INACTIVE_TRACK_COLOR = original_inactive_color
        
    painter.end()

    return QIcon(pixmap)