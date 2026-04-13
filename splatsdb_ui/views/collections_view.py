# SPDX-License-Identifier: GPL-3.0
"""Collections view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QHeaderView,
)
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon


class CollectionsView(QWidget):
    def __init__(self, signals, state):
        super().__init__()
        self.signals = signals
        self.state = state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Collections")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 18px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()

        import_btn = QPushButton("Import")
        import_btn.setIcon(icon("upload", Colors.TEXT))
        header.addWidget(import_btn)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(icon("refresh", Colors.TEXT_DIM))
        refresh_btn.setFixedSize(32, 32)
        header.addWidget(refresh_btn)

        add_btn = QPushButton()
        add_btn.setIcon(icon("plus", Colors.BG))
        add_btn.setFixedSize(32, 32)
        add_btn.setProperty("class", "primary")
        header.addWidget(add_btn)

        del_btn = QPushButton()
        del_btn.setIcon(icon("trash", "#fca5a5"))
        del_btn.setFixedSize(32, 32)
        del_btn.setProperty("danger", "true")
        header.addWidget(del_btn)

        layout.addLayout(header)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Vectors", "Dimension", "Size", "Modified"])
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.tree, stretch=1)

        self.status = QLabel("No collections loaded")
        self.status.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")
        layout.addWidget(self.status)

    def get_params(self) -> list:
        return [
            {"name": "dimension", "label": "Dimension", "type": "spin", "min": 1, "max": 8192, "default": 640},
            {"name": "distance", "label": "Distance", "type": "combo", "options": ["cosine", "l2", "ip"]},
        ]
