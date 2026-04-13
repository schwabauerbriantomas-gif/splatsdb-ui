# SPDX-License-Identifier: GPL-3.0
"""Graph view — knowledge graph visualization."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QComboBox,
    QHeaderView, QSplitter, QFrame,
)
from PySide6.QtCore import Qt
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import GRAPH, SEARCH, REFRESH


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

        refresh_btn = QPushButton(f"{REFRESH}")
        refresh_btn.setFixedSize(32, 32)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Entity search
        search_row = QHBoxLayout()
        self.entity_input = QLineEdit()
        self.entity_input.setPlaceholderText("Search entities...")
        search_row.addWidget(self.entity_input, stretch=1)
        search_btn = QPushButton(f"{SEARCH}")
        search_btn.setFixedSize(32, 32)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        # Splitter: nodes | edges
        splitter = QSplitter(Qt.Horizontal)

        # Nodes tree
        nodes_frame = QFrame()
        nodes_layout = QVBoxLayout(nodes_frame)
        nodes_layout.setContentsMargins(0, 0, 0, 0)
        nodes_layout.addWidget(QLabel("Nodes"))
        self.nodes_tree = QTreeWidget()
        self.nodes_tree.setHeaderLabels(["Entity", "Type", "Connections"])
        self.nodes_tree.header().setStretchLastSection(True)
        nodes_layout.addWidget(self.nodes_tree)
        splitter.addWidget(nodes_frame)

        # Edges tree
        edges_frame = QFrame()
        edges_layout = QVBoxLayout(edges_frame)
        edges_layout.setContentsMargins(0, 0, 0, 0)
        edges_layout.addWidget(QLabel("Edges"))
        self.edges_tree = QTreeWidget()
        self.edges_tree.setHeaderLabels(["Source", "Relation", "Target", "Weight"])
        self.edges_tree.header().setStretchLastSection(True)
        edges_layout.addWidget(self.edges_tree)
        splitter.addWidget(edges_frame)

        splitter.setSizes([500, 500])
        layout.addWidget(splitter, stretch=1)

        # Traversal controls
        traversal = QHBoxLayout()
        traversal.addWidget(QLabel("Max depth:"))
        self.depth_combo = QComboBox()
        self.depth_combo.addItems(["1", "2", "3", "4", "5"])
        traversal.addWidget(self.depth_combo)
        traverse_btn = QPushButton("Traverse")
        traverse_btn.setProperty("class", "primary")
        traversal.addWidget(traverse_btn)
        traversal.addStretch()
        layout.addLayout(traversal)

    def get_params(self) -> list:
        return [
            {"name": "max_neighbors", "label": "Max Neighbors", "type": "spin", "min": 1, "max": 256, "default": 50},
            {"name": "traverse_depth", "label": "Traverse Depth", "type": "spin", "min": 1, "max": 20, "default": 3},
            {"name": "boost_weight", "label": "Boost Weight", "type": "float", "min": 0.0, "max": 1.0, "step": 0.01, "default": 0.5},
        ]
