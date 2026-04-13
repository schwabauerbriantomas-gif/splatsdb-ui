# SPDX-License-Identifier: GPL-3.0
"""Global search bar."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Signal
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon


class GlobalSearchBar(QWidget):
    search_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(48)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(10)

        brand = QLabel("SPLATSDB")
        brand.setStyleSheet(f"""
            color: {Colors.TEXT_DIM};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
        """)
        brand.setFixedWidth(80)
        layout.addWidget(brand)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Search vectors...  Ctrl+K")
        self.input.returnPressed.connect(self._on_search)
        layout.addWidget(self.input, stretch=1)

        self.btn = QPushButton()
        self.btn.setIcon(icon("search", Colors.BG))
        self.btn.setFixedSize(34, 34)
        self.btn.clicked.connect(self._on_search)
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT}; border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT_BRIGHT}; }}
        """)
        layout.addWidget(self.btn)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BG_RAISED};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)

    def _on_search(self):
        text = self.input.text().strip()
        if text:
            self.search_requested.emit(text)

    def focus_search(self):
        self.input.setFocus()
        self.input.selectAll()

    def clear_search(self):
        self.input.clear()
