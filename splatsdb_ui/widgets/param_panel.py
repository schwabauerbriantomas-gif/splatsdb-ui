# SPDX-License-Identifier: GPL-3.0
"""Parameter panel — right sidebar for view-specific controls."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QComboBox, QCheckBox, QSlider, QLineEdit,
    QGroupBox, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt


class ParamWidget(QWidget):
    """A single parameter control (label + widget)."""
    def __init__(self, definition: dict):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(definition.get("label", definition["name"]))
        label.setFixedWidth(120)
        layout.addWidget(label)

        ptype = definition.get("type", "text")
        if ptype == "spin":
            widget = QSpinBox()
            widget.setRange(definition.get("min", 0), definition.get("max", 9999))
            widget.setValue(definition.get("default", 0))
        elif ptype == "combo":
            widget = QComboBox()
            widget.addItems(definition.get("options", []))
        elif ptype == "check":
            widget = QCheckBox()
            widget.setChecked(definition.get("default", False))
        elif ptype == "slider":
            widget = QSlider(Qt.Horizontal)
            widget.setRange(definition.get("min", 0), definition.get("max", 100))
            widget.setValue(definition.get("default", 50))
        else:
            widget = QLineEdit()
            widget.setPlaceholderText(str(definition.get("default", "")))

        layout.addWidget(widget, stretch=1)


class ParamPanel(QWidget):
    """Right sidebar panel — shows view-specific parameters."""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title
        self.title = QLabel("Parameters")
        self.title.setStyleSheet("color: #f9a825; font-weight: 700; font-size: 14px; padding: 4px;")
        layout.addWidget(self.title)

        # Scroll area for params
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.params_layout = QVBoxLayout(self.container)
        self.params_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.container)

        layout.addWidget(self.scroll, stretch=1)

        # Action buttons
        self.action_layout = QVBoxLayout()
        layout.addLayout(self.action_layout)

        # Apply button
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setProperty("class", "primary")
        self.action_layout.addWidget(self.apply_btn)

        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.action_layout.addWidget(self.reset_btn)

    def set_params(self, params: list[dict]):
        """Update the parameter panel with view-specific params."""
        # Clear existing
        for child in self.params_layout.children():
            child.widget().deleteLater()

        # Header
        self.title.setText(f"Parameters")

        for pdef in params:
            pw = ParamWidget(pdef)
            self.params_layout.addWidget(pw)

        # Add stretch at bottom
        self.params_layout.addStretch()
