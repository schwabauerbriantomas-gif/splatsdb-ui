# SPDX-License-Identifier: GPL-3.0
"""Graph view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QLineEdit, QComboBox, QHeaderView, QSplitter, QFrame,
)
from PySide6.QtCore import Qt
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon


class GraphView(QWidget):
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
        title = QLabel("Knowledge Graph")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 18px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton()
        refresh_btn.setIcon(icon("refresh", Colors.TEXT_DIM))
        refresh_btn.setFixedSize(32, 32)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        search_row = QHBoxLayout()
        self.entity_input = QLineEdit()
        self.entity_input.setPlaceholderText("Search entities...")
        search_row.addWidget(self.entity_input, stretch=1)
        search_btn = QPushButton()
        search_btn.setIcon(icon("search", Colors.TEXT))
        search_btn.setFixedSize(32, 32)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        splitter = QSplitter(Qt.Horizontal)

        nodes = QFrame()
        nl = QVBoxLayout(nodes)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.addWidget(QLabel("Nodes"))
        self.nodes_tree = QTreeWidget()
        self.nodes_tree.setHeaderLabels(["Entity", "Type", "Connections"])
        self.nodes_tree.header().setStretchLastSection(True)
        nl.addWidget(self.nodes_tree)
        splitter.addWidget(nodes)

        edges = QFrame()
        el = QVBoxLayout(edges)
        el.setContentsMargins(0, 0, 0, 0)
        el.addWidget(QLabel("Edges"))
        self.edges_tree = QTreeWidget()
        self.edges_tree.setHeaderLabels(["Source", "Relation", "Target", "Weight"])
        self.edges_tree.header().setStretchLastSection(True)
        el.addWidget(self.edges_tree)
        splitter.addWidget(edges)

        splitter.setSizes([500, 500])
        layout.addWidget(splitter, stretch=1)

        traversal = QHBoxLayout()
        traversal.addWidget(QLabel("Max depth:"))
        self.depth_combo = QComboBox()
        self.depth_combo.addItems(["1", "2", "3", "4", "5"])
        traversal.addWidget(self.depth_combo)
        traverse_btn = QPushButton("Traverse")
        traverse_btn.setIcon(icon("arrow-right", Colors.BG))
        traverse_btn.setProperty("class", "primary")
        traversal.addWidget(traverse_btn)
        traversal.addStretch()
        layout.addLayout(traversal)

    def get_params(self) -> list:
        return [
            {"name": "max_neighbors", "label": "Max Neighbors", "type": "spin", "min": 1, "max": 256, "default": 50},
            {"name": "traverse_depth", "label": "Traverse Depth", "type": "spin", "min": 1, "max": 20, "default": 3},
        ]
