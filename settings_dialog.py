from PySide6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QPushButton, QTabWidget, 
    QColorDialog, QDialogButtonBox, QWidget, QVBoxLayout, QLabel,
    QScrollArea, QHBoxLayout
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

import config
from config import APPEARANCE_SPECS, SYSTEM_SETTINGS
from settings_io import load_saved_settings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(700)

        self.fields = {}
        self.saved_settings = load_saved_settings()

        tabs = QTabWidget()
        tabs.addTab(self._build_settings_page(APPEARANCE_SPECS), "Appearance")
        tabs.addTab(self._build_system_page(SYSTEM_SETTINGS), "System")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        outher_layout = QVBoxLayout(self)
        outher_layout.addWidget(tabs)
        outher_layout.addWidget(buttons)
        

    def _build_settings_page(self, specs):
        content = QWidget()
        outer = QVBoxLayout(content)

        columns_widget = QWidget()
        columns_layout = QHBoxLayout(columns_widget)

        left_form = QFormLayout()
        right_form = QFormLayout()

        midpoint = (len(specs) + 1) // 2
        for spec in specs[:midpoint]:
            field = self._build_field(spec)
            self.fields[spec["key"]] = field
            left_form.addRow(spec["label"], field)

        for spec in specs[midpoint:]:
            field = self._build_field(spec)
            self.fields[spec["key"]] = field
            right_form.addRow(spec["label"], field)

        columns_layout.addLayout(left_form)
        columns_layout.addLayout(right_form)

        reset_button = QPushButton("Reset Defaults")
        reset_button.clicked.connect(lambda: self.reset_to_defaults(specs))

        outer.addWidget(columns_widget)
        outer.addWidget(reset_button)

        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        return scroll

    def _build_system_page(self, specs):
        content = QWidget()
        outer = QVBoxLayout(content)

        columns_widget = QWidget()
        columns_layout = QHBoxLayout(columns_widget)

        left_form = QFormLayout()
        right_form = QFormLayout()

        midpoint = (len(specs) + 1) // 2
        for spec in specs[:midpoint]:
            field = self._build_field(spec)
            self.fields[spec["key"]] = field
            left_form.addRow(spec["label"], field)

        for spec in specs[midpoint:]:
            field = self._build_field(spec)
            self.fields[spec["key"]] = field
            right_form.addRow(spec["label"], field)

        columns_layout.addLayout(left_form)
        columns_layout.addLayout(right_form)

        note = QLabel("Changes on this tab take effect after restarting the app.")
        note.setWordWrap(True)

        outer.addWidget(note)
        outer.addWidget(columns_widget)

        reset_button = QPushButton("Reset Defaults")
        reset_button.clicked.connect(lambda: self.reset_to_defaults(SYSTEM_SETTINGS))
        outer.addWidget(reset_button)

        quit_button = QPushButton("Quit App")
        quit_button.clicked.connect(self._quit_app)
        outer.addWidget(quit_button)

        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        return scroll

    def _quit_app(self):
        self.parent().close()

    def _build_field(self, spec):
        current_value = self.saved_settings.get(spec["key"], getattr(config, spec["key"]))

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
        for spec in APPEARANCE_SPECS:
            field = self.fields[spec["key"]]
            if isinstance(field, QSpinBox):
                setattr(config, spec["key"], field.value())
            elif isinstance(field, QPushButton):
                setattr(config, spec["key"], field.property("color"))

    def pending_system_values(self):
        values = {}
        for spec in SYSTEM_SETTINGS:
            field = self.fields[spec["key"]]
            if isinstance(field, QSpinBox):
                values[spec["key"]] = field.value()
        return values


    def reset_to_defaults(self, specs):
        for spec in specs:
            default_value = config.DEFAULT_SETTINGS[spec["key"]]
            field = self.fields[spec["key"]]
            if isinstance(field, QSpinBox):
                field.setValue(default_value)
            elif isinstance(field, QPushButton):
                self._update_color_button(field, default_value)

