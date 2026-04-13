# SPDX-License-Identifier: GPL-3.0
"""Engine Switcher — LM Studio-style backend selector.

Top bar: status dot | engine dropdown | power btn | add btn | gear
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox,
)
from PySide6.QtCore import Signal

from splatsdb_ui.engine_manager import EngineStatus
from splatsdb_ui.utils.icons import PLAY, STOP, DOT_ON, DOT_OFF, DOT_WARN, DOT_ERR, ADD, GEAR
from splatsdb_ui.utils.theme import Colors


STATUS_DOT = {
    EngineStatus.STOPPED:  (DOT_OFF,  Colors.TEXT_MUTED),
    EngineStatus.STARTING: (DOT_WARN, Colors.WARNING),
    EngineStatus.RUNNING:  (DOT_ON,   Colors.SUCCESS),
    EngineStatus.ERROR:    (DOT_ERR,  Colors.ERROR),
}


class EngineSwitcher(QWidget):
    engine_selected = Signal(str)
    start_requested = Signal(str)
    stop_requested = Signal(str)
    add_requested = Signal()
    settings_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(44)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(10)

        # Status dot
        self.status_dot = QLabel(DOT_OFF)
        self.status_dot.setFixedWidth(14)
        self.status_dot.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self.status_dot)

        # Engine combo
        self.engine_combo = QComboBox()
        self.engine_combo.setMinimumWidth(220)
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)
        layout.addWidget(self.engine_combo)

        # Engine type label
        self.type_label = QLabel("")
        self.type_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px; letter-spacing: 0.5px;")
        layout.addWidget(self.type_label)

        layout.addStretch()

        # Power button
        self.power_btn = QPushButton(PLAY)
        self.power_btn.setFixedSize(30, 30)
        self.power_btn.setToolTip("Start / Stop")
        self.power_btn.clicked.connect(self._on_power)
        self._style_power(False)
        layout.addWidget(self.power_btn)

        # Add button
        add_btn = QPushButton(ADD)
        add_btn.setFixedSize(30, 30)
        add_btn.setToolTip("Add engine")
        add_btn.clicked.connect(self.add_requested.emit)
        layout.addWidget(add_btn)

        # Settings
        gear_btn = QPushButton(GEAR)
        gear_btn.setFixedSize(30, 30)
        gear_btn.setToolTip("Engine config")
        gear_btn.clicked.connect(lambda: self.settings_requested.emit(
            self.engine_combo.currentText()))
        gear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {Colors.TEXT_DIM}; font-size: 14px;
                border-radius: 6px;
            }}
            QPushButton:hover {{ color: {Colors.ACCENT}; }}
        """)
        layout.addWidget(gear_btn)

        self.setStyleSheet(f"""
            QWidget {{ background-color: {Colors.BG_RAISED}; border-bottom: 1px solid {Colors.BORDER}; }}
        """)

    def _style_power(self, running: bool):
        if running:
            self.power_btn.setText(STOP)
            self.power_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #991b1b; border: none;
                    border-radius: 6px; color: #fca5a5; font-size: 12px;
                }}
                QPushButton:hover {{ background-color: #b91c1c; }}
            """)
        else:
            self.power_btn.setText(PLAY)
            self.power_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.ACCENT}; border: none;
                    border-radius: 6px; color: {Colors.BG}; font-size: 12px; font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {Colors.ACCENT_BRIGHT}; }}
            """)

    def update_engines(self, engines: list, active_name: str = None):
        self.engine_combo.blockSignals(True)
        self.engine_combo.clear()
        for eng in engines:
            label = f"{eng.name}  ({eng.engine_type})"
            self.engine_combo.addItem(label, eng)
        if active_name:
            idx = self.engine_combo.findText(active_name, match=0)
            if idx < 0:
                for i in range(self.engine_combo.count()):
                    if active_name in self.engine_combo.itemText(i):
                        idx = i
                        break
            if idx >= 0:
                self.engine_combo.setCurrentIndex(idx)
        self.engine_combo.blockSignals(False)

    def update_status(self, name: str, status: EngineStatus):
        symbol, color = STATUS_DOT.get(status, (DOT_OFF, Colors.TEXT_DIM))
        self.status_dot.setText(symbol)
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._style_power(status == EngineStatus.RUNNING)
        self.power_btn.setEnabled(status != EngineStatus.STARTING)

    def _on_engine_changed(self, text: str):
        if text:
            self.engine_selected.emit(text.split("  ")[0])

    def _on_power(self):
        name = self.engine_combo.currentText().split("  ")[0]
        if name:
            self.start_requested.emit(name)
