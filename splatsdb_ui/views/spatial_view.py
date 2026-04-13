# SPDX-License-Identifier: GPL-3.0
"""Spatial view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QComboBox,
)
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon


class SpatialView(QWidget):
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
        title = QLabel("Memory Spaces")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 18px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()

        header.addWidget(QLabel("Wing:"))
        self.wing_combo = QComboBox()
        self.wing_combo.addItems(["All", "Personal", "Work", "Research", "Archive"])
        header.addWidget(self.wing_combo)
        layout.addLayout(header)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Space", "Type", "Vectors", "Created"])
        self.tree.header().setStretchLastSection(True)
        self.tree.setIndentation(24)

        for wing in ["Personal", "Work", "Research"]:
            wing_item = QTreeWidgetItem(self.tree, [wing, "Wing", "0", ""])
            wing_item.setExpanded(True)
            for room in [f"{wing} Room 1", f"{wing} Room 2"]:
                room_item = QTreeWidgetItem(wing_item, [room, "Room", "0", ""])
                for hall in ["Main Hall", "Side Hall"]:
                    QTreeWidgetItem(room_item, [hall, "Hall", "0", ""])

        layout.addWidget(self.tree, stretch=1)

        nav = QHBoxLayout()
        nav_btn = QPushButton("Enter Space")
        nav_btn.setIcon(icon("arrow-right", Colors.BG))
        nav_btn.setProperty("class", "primary")
        nav.addWidget(nav_btn)
        nav.addStretch()
        layout.addLayout(nav)

    def get_params(self) -> list:
        return [{"name": "max_rooms", "label": "Max Rooms/Wing", "type": "spin", "min": 1, "max": 100, "default": 10}]
