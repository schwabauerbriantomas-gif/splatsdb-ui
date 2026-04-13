# SPDX-License-Identifier: GPL-3.0
"""Engine Switcher widget — LM Studio-style backend selector.

Top bar component that shows:
  - Active engine name + status dot
  - Dropdown to switch engines
  - Start/Stop button
  - Add engine button
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QMenu, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QFont, QAction

from splatsdb_ui.engine_manager import EngineStatus


STATUS_COLORS = {
    EngineStatus.STOPPED: "#585b70",
    EngineStatus.STARTING: "#f9e2af",
    EngineStatus.RUNNING: "#a6e3a1",
    EngineStatus.ERROR: "#f38ba8",
}


class EngineSwitcher(QWidget):
    """Engine selector bar — LM Studio style."""

    engine_selected = Signal(str)       # engine name
    start_requested = Signal(str)       # engine name
    stop_requested = Signal(str)        # engine name
    add_requested = Signal()
    settings_requested = Signal(str)    # engine name

    def __init__(self):
        super().__init__()
        self.setFixedHeight(42)
        self._build_ui()

        self.setStyleSheet("""
            QWidget {
                background-color: #181825;
                border-bottom: 1px solid #313244;
            }
        """)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(8)

        # Status dot
        self.status_dot = QLabel("●")
        self.status_dot.setFixedWidth(16)
        self.status_dot.setStyleSheet("color: #585b70; font-size: 14px;")
        layout.addWidget(self.status_dot)

        # Engine selector combo
        self.engine_combo = QComboBox()
        self.engine_combo.setMinimumWidth(200)
        self.engine_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 13px;
                font-weight: 600;
            }
            QComboBox:hover { border-color: #f9a825; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                selection-background-color: #f9a825;
                selection-color: #1e1e2e;
            }
        """)
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)
        layout.addWidget(self.engine_combo)

        # Engine type label
        self.type_label = QLabel("")
        self.type_label.setStyleSheet("color: #585b70; font-size: 11px;")
        layout.addWidget(self.type_label)

        # Start/Stop button
        self.power_btn = QPushButton("▶")
        self.power_btn.setFixedSize(32, 32)
        self.power_btn.setToolTip("Start/Stop engine")
        self.power_btn.clicked.connect(self._on_power_clicked)
        self.power_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #94e2d5; }
        """)
        layout.addWidget(self.power_btn)

        # Add engine button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(32, 32)
        add_btn.setToolTip("Add new engine")
        add_btn.clicked.connect(self.add_requested.emit)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 16px;
                font-size: 16px;
                font-weight: bold;
                color: #cdd6f4;
            }
            QPushButton:hover { border-color: #f9a825; color: #f9a825; }
        """)
        layout.addWidget(add_btn)

        # Settings gear
        gear_btn = QPushButton("⚙")
        gear_btn.setFixedSize(32, 32)
        gear_btn.setToolTip("Engine settings")
        gear_btn.clicked.connect(self._on_settings)
        gear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                color: #585b70;
            }
            QPushButton:hover { color: #f9a825; }
        """)
        layout.addWidget(gear_btn)

        layout.addStretch()

    def update_engines(self, engines: list, active_name: str = None):
        """Refresh the engine list."""
        self.engine_combo.blockSignals(True)
        self.engine_combo.clear()
        for eng in engines:
            self.engine_combo.addItem(eng.name, eng)
        if active_name:
            idx = self.engine_combo.findText(active_name)
            if idx >= 0:
                self.engine_combo.setCurrentIndex(idx)
        self.engine_combo.blockSignals(False)
        self._on_engine_changed(self.engine_combo.currentText())

    def update_status(self, name: str, status: EngineStatus):
        """Update status dot and power button for an engine."""
        color = STATUS_COLORS.get(status, "#585b70")
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")

        if status == EngineStatus.RUNNING:
            self.power_btn.setText("■")
            self.power_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f38ba8;
                    border: none;
                    border-radius: 16px;
                    font-size: 12px;
                    font-weight: bold;
                    color: #1e1e2e;
                }
                QPushButton:hover { background-color: #eba0ac; }
            """)
        elif status == EngineStatus.STARTING:
            self.power_btn.setText("⏳")
            self.power_btn.setEnabled(False)
        else:
            self.power_btn.setText("▶")
            self.power_btn.setEnabled(True)
            self.power_btn.setStyleSheet("""
                QPushButton {
                    background-color: #a6e3a1;
                    border: none;
                    border-radius: 16px;
                    font-size: 14px;
                    font-weight: bold;
                    color: #1e1e2e;
                }
                QPushButton:hover { background-color: #94e2d5; }
            """)

    def _on_engine_changed(self, name: str):
        if name:
            self.engine_selected.emit(name)

    def _on_power_clicked(self):
        name = self.engine_combo.currentText()
        if name:
            # Toggle based on current state — caller decides
            self.start_requested.emit(name)

    def _on_settings(self):
        name = self.engine_combo.currentText()
        if name:
            self.settings_requested.emit(name)
