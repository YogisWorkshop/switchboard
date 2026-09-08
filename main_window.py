from PySide6.QtWidgets import (
    QMainWindow, QGraphicsView, QWidget, QFrame,
    QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer, QSize

from panel_scene import PanelScene
from tile_registry import TILE_CLASSES
from layout_io import save_layout, load_layout
from settings_io import save_settings, load_settings
from tile_icon import render_tile_icon
from properties_dialog import PropertiesDialog
from settings_dialog import SettingsDialog
import config
from config import (GRID_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT,
                    PANEL_COLS,PANEL_ROWS, GEAR_SIZE, GEAR_ICON_PATH,
                    PanelMode, Tool)    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        load_settings()

        self.setWindowTitle("Switchboard")
        self.resize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.setStyleSheet(f"background-color: {config.BACKGROUND_COLOR};")

        self.scene = PanelScene(GRID_SIZE)
        self.scene.setSceneRect(0, 0, PANEL_COLS * GRID_SIZE, PANEL_ROWS * GRID_SIZE)

        self.view = QGraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.view.setFrameShape(QFrame.Shape.NoFrame)

        # Floating gear button
        self.edit_button = QPushButton(self.view)
        self.edit_button.setIcon(QIcon(GEAR_ICON_PATH))
        self.edit_button.setIconSize(QSize(GEAR_SIZE, GEAR_SIZE))
        self.edit_button.setFixedSize(GEAR_SIZE + 10, GEAR_SIZE + 10)
        self.edit_button.setFlat(True)
        self.edit_button.setStyleSheet("border: none; background: transparent;")
        self.edit_button.clicked.connect(self.toggle_mode)

        self.tile_palette = self._build_tile_palette()
        self.tool_palette = self._build_tool_palette()

        self.scene.selection_changed.connect(self.on_selection_changed)
        load_layout(self.scene)

        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.addWidget(self.view)
        top_layout.addWidget(self.tile_palette)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        container = QWidget()
        outer_layout = QVBoxLayout(container)
        outer_layout.addWidget(top_row)
        outer_layout.addWidget(self.tool_palette)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.setCentralWidget(container)

        self.set_mode(PanelMode.OPERATE)

    def _build_tile_palette(self):
        palette = QWidget()
        grid = QGridLayout(palette)
        grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        button_size = GRID_SIZE + 10
        spacing = 1
        margin = 0

        grid.setSpacing(spacing)
        grid.setContentsMargins(margin, margin, margin, margin)

        tile_types = list(TILE_CLASSES.values())
        colums = 2

        self.place_buttons = {}
        for index, tile_type in enumerate(tile_types):
            button = QPushButton()
            button.setIcon(render_tile_icon(tile_type()))
            button.setIconSize(QSize(GRID_SIZE, GRID_SIZE))
            button.setFixedSize(GRID_SIZE + 10, GRID_SIZE + 10)
            button.setCheckable(True)
            button.setStyleSheet(f"""
                        QPushButton:checked {{
                            background-color: {config.SELECTION_HIGHLIGHT_COLOR}
                        }}
                    """)
            button.clicked.connect(lambda checked, t=tile_type: self.arm_place(t))

            row, col = divmod(index, colums)
            grid.addWidget(button, row, col)

            self.place_buttons[tile_type] = button

        pallete_width = colums * button_size + (colums -1) * spacing + 2 * margin
        palette.setFixedWidth(pallete_width)
        return palette

    def _build_tool_palette(self):
        palette = QWidget()
        layout = QHBoxLayout(palette)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.toggle_mode)

        self.rotate_button = QPushButton("Rotate")
        self.rotate_button.clicked.connect(self.rotate_selected)

        self.move_button = QPushButton("Move")
        self.move_button.setCheckable(True)
        self.move_button.clicked.connect(self.arm_move)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_selected)

        self.properties_button = QPushButton("Properties")
        self.properties_button.clicked.connect(self.open_properties)

        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings)


        for button in [
            self.exit_button, self.rotate_button, self.move_button,
            self.delete_button, self.properties_button, self.settings_button,
        ]:
            layout.addWidget(button)

        self.selection_buttons = [
            self.rotate_button, self.move_button,
            self.delete_button, self.properties_button
        ]
        self.set_selection_buttons_enabeled(False)

        return palette


    def showEvent(self, event):
        super().showEvent(event)
        self.view.horizontalScrollBar().setValue(0)
        self.view.verticalScrollBar().setValue(0)
        self.fit_scene_to_view()
        self.position_edit_button()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_scene_to_view()
        self.position_edit_button()

    def fit_scene_to_view(self):
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def position_edit_button(self):
        margin = 10
        x = self.view.width() - self.edit_button.width() - margin
        y = self.view.height() - self.edit_button.height() - margin
        self.edit_button.move(x, y)

    def set_mode(self, mode):
        if self.scene.mode == PanelMode.EDIT and mode == PanelMode.OPERATE:
            save_layout(self.scene)

        self.scene.mode = mode
        self.scene.tool = Tool.SELECT
        self.scene.armed_tile_type = None
        self.scene.clear_selection()
        self.tile_palette.setVisible(mode == PanelMode.EDIT)
        self.tool_palette.setVisible(mode == PanelMode.EDIT)
        self.edit_button.setVisible(mode == PanelMode.OPERATE)
        self.update_tool_buttons()
        QTimer.singleShot(0, self.fit_scene_to_view)
        QTimer.singleShot(0, self.position_edit_button)
        print(f"Mode: {mode.name}")

    def toggle_mode(self):
        new_mode = PanelMode.OPERATE if self.scene.mode == PanelMode.EDIT else PanelMode.EDIT
        self.set_mode(new_mode)
        
    def arm_place(self, tile_type):
        self.scene.clear_selection()
        if self.scene.tool == Tool.PLACE and self.scene.armed_tile_type == tile_type:
            self.scene.tool = Tool.SELECT
            self.scene.armed_tile_type = None
            print("Disarmed")
        else:
            self.scene.tool = Tool.PLACE
            self.scene.armed_tile_type = tile_type
            print(f"Aarmed: place {tile_type.__name__}")
        self.update_tool_buttons()

    def arm_move(self):
        if self.scene.tool == Tool.MOVE:
            self.scene.tool = Tool.SELECT
            print("Disarmed move")
        else:
            if self.scene.selected_tile is None:
                return
            self.scene.tool = Tool.MOVE
            print("Amred: move")
        self.update_tool_buttons()

    def disarm_tool(self):
        self.scene.tool = Tool.SELECT
        self.scene.armed_tile_type = None
        self.update_tool_buttons()

    def rotate_selected(self):
        if self.scene.selected_tile is None:
            return
        self.scene.selected_tile.rotate_cw()
        self.disarm_tool()

    def delete_selected(self):
        if self.scene.selected_tile is None:
            return
        self.scene.remove_tile(self.scene.selected_tile)
        self.disarm_tool()

    def open_properties(self):
        if self.scene.selected_tile is None:
            return

        tile = self.scene.selected_tile
        dialog = PropertiesDialog(tile, parent=self)
        if dialog.exec() == PropertiesDialog.DialogCode.Accepted:
            dialog.apply_to_tile()
            tile.update()

        self.disarm_tool()

    def open_settings(self):
        dialog = SettingsDialog(parent=self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            dialog.apply_settings()
            save_settings()
            self.scene.update()
            self.refresh_tile_icons()

    def set_selection_buttons_enabeled(self, enabled):
        for button in self.selection_buttons:
            button.setEnabled(enabled)

    def on_selection_changed(self, title):
        self.set_selection_buttons_enabeled(title is not None)

    def update_tool_buttons(self):
        for tile_type, button in self.place_buttons.items():
            button.setChecked(
                self.scene.tool == Tool.PLACE and self.scene.armed_tile_type == tile_type
            )
        self.move_button.setChecked(self.scene.tool == Tool.MOVE)

    def refresh_tile_icons(self):
        for tile_type, button in self.place_buttons.items():
            button.setIcon(render_tile_icon(tile_type()))