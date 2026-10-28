from PySide6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QLineEdit, QComboBox, 
    QDialogButtonBox, QCheckBox,
)
from PySide6.QtCore import QSize

class PropertiesDialog(QDialog):
    def __init__(self, tile, parent=None):
        super().__init__(parent)
        self.tile = tile
        self.setMinimumSize(QSize(400, 300))

        title = getattr(tile, "label", "") or tile.__class__.__name__
        self.setWindowTitle(f"{title} Properties")

        self.fields = {}

        layout = QFormLayout(self)

        for spec in tile.property_specs:
            field = self._build_field(spec)
            self.fields[spec["key"]] = field
            layout.addRow(spec["label"], field)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _build_field(self, spec):
        current_value = getattr(self.tile, spec["key"])

        if spec["type"] == int:
            field = QSpinBox()
            field.setRange(0, 9999)
            field.setValue(current_value)
            return field

        if spec["type"] == str:
            field = QLineEdit()
            field.setText(current_value)
            if "max_length" in spec:
                field.setMaxLength(spec["max_length"])
            return field

        if spec["type"] == "choice":
            field = QComboBox()
            field.addItems(spec["choices"])
            field.setCurrentText(current_value)
            return field

        if spec["type"] == bool:
            field = QCheckBox()
            field.setChecked(current_value)
            return field


        raise ValueError(f"Unsupported property type: {spec['type']}")

    def apply_to_tile(self):
        old_label = getattr(self.tile, "label", None)
        for key, field in self.fields.items():
            if isinstance(field, QSpinBox):
                setattr(self.tile, key, field.value())
            elif isinstance(field, QLineEdit):
                setattr(self.tile, key, field.text())
            elif isinstance(field, QComboBox):
                setattr(self.tile, key, field.currentText())
            elif isinstance(field, QCheckBox):
                setattr(self.tile, key, field.isChecked())
        new_label = getattr(self.tile, "label", None)
        scene = self.tile.scene()
        if scene is not None and old_label and new_label != old_label \
                and not getattr(self.tile, "lined_to", ""):
            scene.relink(old_label, new_label)