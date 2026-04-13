# SPDX-License-Identifier: GPL-3.0
"""IO Tray — input/output thumbnails at bottom."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QVBoxLayout,
)
from PySide6.QtCore import Qt
from splatsdb_ui.utils.theme import Colors


class IOTray(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)

        header = QHBoxLayout()
        lbl = QLabel("IO TRAY")
        lbl.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 10px; font-weight: 700; letter-spacing: 1.0px;")
        header.addWidget(lbl)
        header.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.items_widget = QWidget()
        self.items_layout = QHBoxLayout(self.items_widget)
        self.items_layout.setAlignment(Qt.AlignLeft)
        self.scroll.setWidget(self.items_widget)
        layout.addWidget(self.scroll)

        self.setStyleSheet(f"background-color: {Colors.BG_RAISED}; border-top: 1px solid {Colors.BORDER};")
