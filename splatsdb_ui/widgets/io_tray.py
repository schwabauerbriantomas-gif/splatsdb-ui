# SPDX-License-Identifier: GPL-3.0
"""IO Tray widget — input/output thumbnails at the bottom."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QVBoxLayout,
)
from PySide6.QtCore import Qt


class IOTray(QWidget):
    """Bottom panel showing input/output file thumbnails and status."""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("IO Tray"))
        header.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        # Scroll area for items
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.items_widget = QWidget()
        self.items_layout = QHBoxLayout(self.items_widget)
        self.items_layout.setAlignment(Qt.AlignLeft)
        self.scroll.setWidget(self.items_widget)

        layout.addWidget(self.scroll)

        self.setStyleSheet("""
            QWidget {
                background-color: #181825;
                border-top: 1px solid #313244;
            }
        """)
