# SPDX-License-Identifier: GPL-3.0
"""Graph view — knowledge graph visualization and management."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QLineEdit,
    QComboBox, QTextEdit, QSplitter, QHeaderView,
)
from PySide6.QtCore import Qt, Signal

from splatsdb_ui.utils.signals import SignalBus
from splatsdb_ui.utils.state import AppState


class GraphView(QWidget):
    """Knowledge graph view — nodes, edges, traversal, entity search."""

    def __init__(self, signals: SignalBus, state: AppState):
        super().__init__()
        self.signals = signals
        self.state = state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Knowledge Graph")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()

        stats_btn = QPushButton("📊 Stats")
        stats_btn.clicked.connect(self._on_stats)
        header.addWidget(stats_btn)

        layout.addLayout(header)

        # Main splitter: graph canvas + side panel
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, stretch=1)

        # Left: Graph canvas (placeholder for future QPainter visualization)
        self.graph_canvas = QLabel("Graph Visualization Canvas\n(nodes and edges will render here)")
        self.graph_canvas.setAlignment(Qt.AlignCenter)
        self.graph_canvas.setStyleSheet("""
            background-color: #181825;
            border: 1px solid #313244;
            border-radius: 8px;
            color: #585b70;
            font-size: 16px;
            padding: 40px;
        """)
        splitter.addWidget(self.graph_canvas)

        # Right: Controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)

        # Add node
        add_group = QGroupBox("Add Node")
        add_layout = QVBoxLayout(add_group)
        add_layout.addWidget(QLabel("Text:"))
        self.node_text = QLineEdit()
        self.node_text.setPlaceholderText("Document or entity text...")
        add_layout.addWidget(self.node_text)
        add_layout.addWidget(QLabel("Type:"))
        self.node_type = QComboBox()
        self.node_type.addItems(["document", "entity", "default"])
        add_layout.addWidget(self.node_type)
        add_btn = QPushButton("Add Node")
        add_btn.setProperty("class", "primary")
        add_layout.addWidget(add_btn)
        right_layout.addWidget(add_group)

        # Add relation
        rel_group = QGroupBox("Add Relation")
        rel_layout = QVBoxLayout(rel_group)
        rel_layout.addWidget(QLabel("Source ID:"))
        self.rel_source = QLineEdit()
        rel_layout.addWidget(self.rel_source)
        rel_layout.addWidget(QLabel("Target ID:"))
        self.rel_target = QLineEdit()
        rel_layout.addWidget(self.rel_target)
        rel_layout.addWidget(QLabel("Type:"))
        self.rel_type = QLineEdit()
        self.rel_type.setPlaceholderText("e.g. related_to, authored_by")
        rel_layout.addWidget(self.rel_type)
        add_rel_btn = QPushButton("Add Relation")
        add_rel_btn.clicked.connect(self._on_add_relation)
        rel_layout.addWidget(add_rel_btn)
        right_layout.addWidget(rel_group)

        # Graph traversal
        trav_group = QGroupBox("Traverse")
        trav_layout = QVBoxLayout(trav_group)
        trav_layout.addWidget(QLabel("Start from query:"))
        self.trav_query = QLineEdit()
        self.trav_query.setPlaceholderText("Text to find start node...")
        trav_layout.addWidget(self.trav_query)
        trav_layout.addWidget(QLabel("Max depth:"))
        self.trav_depth = QLineEdit("3")
        trav_layout.addWidget(self.trav_depth)
        trav_btn = QPushButton("Traverse")
        trav_btn.clicked.connect(self._on_traverse)
        trav_layout.addWidget(trav_btn)
        right_layout.addWidget(trav_group)

        right_layout.addStretch()
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 300])

    def _on_stats(self):
        self.signals.status_message.emit("Loading graph stats...")

    def _on_add_relation(self):
        self.signals.status_message.emit("Adding relation...")

    def _on_traverse(self):
        self.signals.status_message.emit("Traversing graph...")

    def get_params(self) -> list[dict]:
        return [
            {"name": "max_depth", "label": "Max Depth", "type": "spin", "min": 1, "max": 10, "default": 3},
            {"name": "search_type", "label": "Search Type", "type": "combo",
             "options": ["hybrid", "entity", "vector"]},
        ]
