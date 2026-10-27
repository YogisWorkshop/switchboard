from PySide6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QLineEdit, QComboBox, QPushButton,
    QTabWidget, QColorDialog, QDialogButtonBox, QWidget, QVBoxLayout,
    QLabel, QScrollArea, QHBoxLayout
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

import config
from config import APPEARANCE_SPECS, SYSTEM_SETTINGS, INTERFACE_SETTINGS
from settings_io import load_saved_settings


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(700)

        self.fields = {}   # key -> widget
        self.forms = {}    # key -> the QFormLayout holding that row
        self.saved_settings = load_saved_settings()

        quit_button = QPushButton("Quit App")
        quit_button.clicked.connect(self._quit_app)

        tabs = QTabWidget()
        tabs.addTab(self._build_page(APPEARANCE_SPECS), "Appearance")
        tabs.addTab(self._build_page(INTERFACE_SETTINGS, columns=1), "Interface")
        tabs.addTab(
            self._build_page(
                SYSTEM_SETTINGS,
                note="Changes on this tab take effect after restarting the app.",
                extra_buttons=[quit_button],
            ),
            "System",
        )

        self.fields["STATION_TYPE"].currentTextChanged.connect(
            lambda _text: self._update_station_rows()
        )
        self._update_station_rows()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(tabs)
        outer_layout.addWidget(buttons)

    # ---- building pages -------------------------------------------------

    def _build_page(self, specs, columns=2, note=None, extra_buttons=()):
        content = QWidget()
        outer = QVBoxLayout(content)

        if note:
            note_label = QLabel(note)
            note_label.setWordWrap(True)
            outer.addWidget(note_label)

        columns_widget = QWidget()
        columns_layout = QHBoxLayout(columns_widget)

        per_column = -(-len(specs) // columns)   # ceiling division
        for start in range(0, len(specs), per_column):
            form = QFormLayout()
            for spec in specs[start:start + per_column]:
                field = self._build_field(spec)
                self.fields[spec["key"]] = field
                self.forms[spec["key"]] = form
                form.addRow(spec["label"], field)
            columns_layout.addLayout(form)

        outer.addWidget(columns_widget)

        reset_button = QPushButton("Reset Defaults")
        reset_button.clicked.connect(lambda: self.reset_to_defaults(specs))
        outer.addWidget(reset_button)

        for button in extra_buttons:
            outer.addWidget(button)

        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return scroll

    def _build_field(self, spec):
        current_value = self.saved_settings.get(spec["key"], getattr(config, spec["key"]))

        if spec["type"] == int:
            field = QSpinBox()
            field.setRange(spec["min"], spec["max"])
            field.setValue(current_value)
            return field

        if spec["type"] == str:
            field = QLineEdit()
            field.setText(current_value)
            return field

        if spec["type"] == "choice":
            field = QComboBox()
            field.addItems(spec["choices"])
            field.setCurrentText(current_value)
            return field

        if spec["type"] == "color":
            field = QPushButton()
            self._update_color_button(field, current_value)
            field.clicked.connect(lambda: self._pick_color(field))
            return field

        raise ValueError(f"Unsupported setting type: {spec['type']}")

    # ---- reading and writing field values --------------------------------

    def _field_value(self, field):
        if isinstance(field, QSpinBox):
            return field.value()
        if isinstance(field, QLineEdit):
            return field.text()
        if isinstance(field, QComboBox):
            return field.currentText()
        return field.property("color")   # the color QPushButton

    def _set_field_value(self, field, value):
        if isinstance(field, QSpinBox):
            field.setValue(value)
        elif isinstance(field, QLineEdit):
            field.setText(value)
        elif isinstance(field, QComboBox):
            field.setCurrentText(value)
        else:
            self._update_color_button(field, value)

    # ---- color button ----------------------------------------------------

    def _update_color_button(self, button, color_hex):
        button.setProperty("color", color_hex)
        button.setStyleSheet(f"background-color: {color_hex};")

    def _pick_color(self, button):
        current = QColor(button.property("color"))
        color = QColorDialog.getColor(current, self)
        if color.isValid():
            self._update_color_button(button, color.name())

    # ---- interface tab: show only the rows that fit the station ----------

    def _update_station_rows(self):
        station = self._field_value(self.fields["STATION_TYPE"])
        for spec in INTERFACE_SETTINGS:
            stations = spec.get("stations")
            if stations is None:
                continue
            self.forms[spec["key"]].setRowVisible(
                self.fields[spec["key"]], station in stations
            )

    # ---- results ---------------------------------------------------------

    def apply_settings(self):
        """Appearance and interface values go live right away."""
        for spec in APPEARANCE_SPECS + INTERFACE_SETTINGS:
            setattr(config, spec["key"], self._field_value(self.fields[spec["key"]]))

    def pending_system_values(self):
        """System values are only written to settings.json (restart needed)."""
        return {
            spec["key"]: self._field_value(self.fields[spec["key"]])
            for spec in SYSTEM_SETTINGS
        }

    def reset_to_defaults(self, specs):
        for spec in specs:
            self._set_field_value(
                self.fields[spec["key"]], config.DEFAULT_SETTINGS[spec["key"]]
            )

    def _quit_app(self):
        self.parent().close()