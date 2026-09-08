from PySide6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QPushButton, QTabWidget, 
    QColorDialog, QDialogButtonBox, QWidget, QVBoxLayout, QLabel
)
from PySide6.QtGui import QColor

import config
from config import APPEARANCE_SPECS, SYSTEM_SETTINGS

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        self.fields = {}

        tabs = QTabWidget()
        tabs.addTab(self._build_settings_page(APPEARANCE_SPECS), "Appearance")
        tabs.addTab(self._build_system_page(), "System")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        outher_layout = QVBoxLayout(self)
        outher_layout.addWidget(tabs)
        outher_layout.addWidget(buttons)
        

    def _build_settings_page(self, specs):
        page = QWidget()
        layout = QFormLayout(page)
        for spec in specs:
            field = self._build_field(spec)
            self.fields[spec["key"]] = field
            layout.addRow(spec["label"], field)

        reset_button = QPushButton("Reset Defaults")
        reset_button.clicked.connect(lambda: self.reset_to_defaults(specs))
        layout.addRow(reset_button)
        
        return page

    def _build_system_page(self):
        page = QWidget()
        layout = QFormLayout(page)

        note = QLabel("Changes on this tab take effect after restarting the app.")
        note.setWordWrap(True)
        layout.addRow(note)

        for spec in SYSTEM_SETTINGS:
            field = self._build_field(spec)
            self.fields[spec["key"]] = field
            layout.addRow(spec["label"], field)

        reset_button = QPushButton("Reset Defaults")
        reset_button.clicked.connect(lambda: self.reset_to_defaults(SYSTEM_SETTINGS))
        layout.addRow(reset_button)

        quit_button = QPushButton("Quit App")
        quit_button.clicked.connect(self._quit_app)
        layout.addRow(quit_button)

        return page

    def _quit_app(self):
        self.parent().close()

    def _build_field(self, spec):
        current_value = getattr(config, spec["key"])

        if spec["type"] == int:
            field = QSpinBox()
            field.setRange(spec["min"], spec["max"])
            field.setValue(current_value)
            return field

        if spec["type"] == "color":
            field = QPushButton()
            field.setProperty("color", current_value)
            self._update_color_button(field, current_value)
            field.clicked.connect(lambda: self._pick_color(field))
            return field

        raise ValueError(f"Unsupported setting type: {spec['type']}")

    def _update_color_button(self, button, color_hex):
        button.setProperty("color", color_hex)
        button.setStyleSheet(f"background-color: {color_hex};")

    def _pick_color(self, button):
        current = QColor(button.property("color"))
        color = QColorDialog.getColor(current, self)
        if color.isValid():
            self._update_color_button(button, color.name())

    def apply_settings(self):
        for key, field in self.fields.items():
            if isinstance(field, QSpinBox):
                setattr(config, key, field.value())
            elif isinstance(field, QPushButton):
                setattr(config, key, field.property("color"))

    def reset_to_defaults(self, specs):
        for spec in specs:
            default_value = config.DEFAULT_SETTINGS[spec["key"]]
            field = self.fields[spec["key"]]
            if isinstance(field, QSpinBox):
                field.setValue(default_value)
            elif isinstance(field, QPushButton):
                self._update_color_button(field, default_value)

