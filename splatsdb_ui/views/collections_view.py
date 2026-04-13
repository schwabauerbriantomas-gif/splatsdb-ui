# SPDX-License-Identifier: GPL-3.0
"""Collections view — manage vector collections and shards."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import COLLECTION, REFRESH, ADD, REMOVE, FILE


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

        # Header
        header = QHBoxLayout()
        title = QLabel("Collections")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 18px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()

        import_btn = QPushButton(f"{FILE} Import")
        header.addWidget(import_btn)

        refresh_btn = QPushButton(f"{REFRESH}")
        refresh_btn.setFixedSize(32, 32)
        header.addWidget(refresh_btn)

        add_btn = QPushButton(f"{ADD}")
        add_btn.setFixedSize(32, 32)
        add_btn.setProperty("class", "primary")
        header.addWidget(add_btn)

        del_btn = QPushButton(f"{REMOVE}")
        del_btn.setFixedSize(32, 32)
        del_btn.setProperty("danger", True)
        header.addWidget(del_btn)

        layout.addLayout(header)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Vectors", "Dimension", "Size", "Modified"])
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.setAlternatingRowColors(False)
        self.tree.setIndentation(20)

        layout.addWidget(self.tree, stretch=1)

        # Status
        self.status = QLabel("No collections loaded")
        self.status.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")
        layout.addWidget(self.status)

    def get_params(self) -> list:
        return [
            {"name": "dimension", "label": "Dimension", "type": "spin", "min": 1, "max": 8192, "default": 640},
            {"name": "distance", "label": "Distance", "type": "combo", "options": ["cosine", "l2", "ip"], "default": "cosine"},
        ]
