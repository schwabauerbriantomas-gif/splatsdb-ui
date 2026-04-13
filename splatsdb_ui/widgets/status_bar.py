# SPDX-License-Identifier: GPL-3.0
"""Status bar — connection, model, stats."""

from PySide6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import DOT_ON, DOT_OFF, PIPE


class SplatsDBStatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        # Connection
        self.conn_label = QLabel(f"{DOT_OFF} Disconnected")
        self.conn_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")
        self.addWidget(self.conn_label)

        self._add_sep()

        # Model / Preset
        self.model_label = QLabel("No engine")
        self.model_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")
        self.addWidget(self.model_label)

        self._add_sep()

        # Document count
        self.doc_label = QLabel("0 vectors")
        self.doc_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")
        self.addWidget(self.doc_label)

        self._add_sep()

        # GPU
        self.gpu_label = QLabel("CPU")
        self.gpu_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")
        self.addPermanentWidget(self.gpu_label)

    def _add_sep(self):
        sep = QLabel(PIPE)
        sep.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px; margin: 0 6px;")
        self.addWidget(sep)

    def set_connected(self, connected: bool, preset: str = ""):
        if connected:
            self.conn_label.setText(f"{DOT_ON} Connected")
            self.conn_label.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 11px;")
        else:
            self.conn_label.setText(f"{DOT_OFF} Disconnected")
            self.conn_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")

    def set_model(self, name: str):
        self.model_label.setText(name or "No engine")

    def set_doc_count(self, count: int):
        self.doc_label.setText(f"{count:,} vectors")

    def set_gpu(self, info: str):
        self.gpu_label.setText(info)

    def show_message(self, msg: str, timeout: int = 4000):
        self.showMessage(msg, timeout)
