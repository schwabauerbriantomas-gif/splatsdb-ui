# SPDX-License-Identifier: GPL-3.0
"""Spatial view — Wing/Room/Hall memory navigator."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QComboBox,
)
from PySide6.QtCore import Qt
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import SPATIAL, SEARCH


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

        # Wing selector
        header.addWidget(QLabel("Wing:"))
        self.wing_combo = QComboBox()
        self.wing_combo.addItems(["All", "Personal", "Work", "Research", "Archive"])
        header.addWidget(self.wing_combo)
        layout.addLayout(header)

        # Tree: Wing > Room > Hall
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Space", "Type", "Vectors", "Created"])
        self.tree.header().setStretchLastSection(True)
        self.tree.setIndentation(24)

        # Sample structure
        for wing_name in ["Personal", "Work", "Research"]:
            wing_item = QTreeWidgetItem(self.tree, [wing_name, "Wing", "0", ""])
            wing_item.setExpanded(True)
            for room_name in [f"{wing_name} Room 1", f"{wing_name} Room 2"]:
                room_item = QTreeWidgetItem(wing_item, [room_name, "Room", "0", ""])
                for hall_name in ["Main Hall", "Side Hall"]:
                    QTreeWidgetItem(room_item, [hall_name, "Hall", "0", ""])

        layout.addWidget(self.tree, stretch=1)

        # Navigation
        nav = QHBoxLayout()
        nav.addWidget(QLabel("Navigate:"))
        nav_btn = QPushButton("Enter Space")
        nav_btn.setProperty("class", "primary")
        nav.addWidget(nav_btn)
        nav.addStretch()
        layout.addLayout(nav)

    def get_params(self) -> list:
        return [
            {"name": "max_rooms", "label": "Max Rooms/Wing", "type": "spin", "min": 1, "max": 100, "default": 10},
        ]
