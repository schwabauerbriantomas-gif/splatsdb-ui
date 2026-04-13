# SPDX-License-Identifier: GPL-3.0
"""Global search bar widget."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel,
)
from PySide6.QtCore import Signal, Qt


class GlobalSearchBar(QWidget):
    """Global search bar at the top of the main window."""

    search_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(48)
        self._build_ui()

        self.setStyleSheet("""
            QWidget {
                background-color: #181825;
                border-bottom: 1px solid #313244;
            }
        """)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)

        # App icon / label
        icon = QLabel("🔶")
        icon.setFixedWidth(30)
        layout.addWidget(icon)

        # Search input
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search SplatsDB... (Ctrl+K)")
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 20px;
                padding: 6px 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #f9a825;
            }
        """)
        self.input.returnPressed.connect(self._on_search)
        layout.addWidget(self.input, stretch=1)

        # Search button
        self.btn = QPushButton("🔍")
        self.btn.setFixedSize(36, 36)
        self.btn.clicked.connect(self._on_search)
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #f9a825;
                border: none;
                border-radius: 18px;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #fbc02d; }
        """)
        layout.addWidget(self.btn)

    def _on_search(self):
        text = self.input.text().strip()
        if text:
            self.search_requested.emit(text)

    def focus_search(self):
        self.input.setFocus()
        self.input.selectAll()

    def clear_search(self):
        self.input.clear()
