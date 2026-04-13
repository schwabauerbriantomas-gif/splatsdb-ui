# SPDX-License-Identifier: GPL-3.0
"""Cluster view — distributed cluster dashboard."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QComboBox, QProgressBar,
)
from PySide6.QtCore import Qt

from splatsdb_ui.utils.signals import SignalBus
from splatsdb_ui.utils.state import AppState


class ClusterView(QWidget):
    """Cluster dashboard — nodes, routing, sharding, benchmarks."""

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
        title = QLabel("Cluster Dashboard")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._on_refresh)
        header.addWidget(refresh_btn)

        reset_btn = QPushButton("🗑️ Reset")
        reset_btn.setProperty("class", "danger")
        reset_btn.clicked.connect(self._on_reset)
        header.addWidget(reset_btn)

        layout.addLayout(header)

        # Join node
        join_group = QGroupBox("Join Node")
        join_layout = QHBoxLayout(join_group)
        join_layout.addWidget(QLabel("ID:"))
        self.node_id = QLineEdit()
        self.node_id.setPlaceholderText("node-1")
        join_layout.addWidget(self.node_id)
        join_layout.addWidget(QLabel("URL:"))
        self.node_url = QLineEdit()
        self.node_url.setPlaceholderText("localhost:8001")
        join_layout.addWidget(self.node_url)
        join_layout.addWidget(QLabel("Role:"))
        self.node_role = QComboBox()
        self.node_role.addItems(["worker", "edge", "coordinator"])
        join_layout.addWidget(self.node_role)
        join_btn = QPushButton("Join")
        join_btn.setProperty("class", "primary")
        join_layout.addWidget(join_btn)
        layout.addWidget(join_group)

        # Nodes table
        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(6)
        self.nodes_table.setHorizontalHeaderLabels([
            "Node ID", "URL", "Role", "Weight", "Status", "Shards"
        ])
        self.nodes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.nodes_table.setAlternatingRowColors(True)
        layout.addWidget(self.nodes_table, stretch=1)

        # Benchmark row
        bench_row = QHBoxLayout()
        bench_row.addWidget(QLabel("Benchmark:"))
        self.bench_n = QLineEdit("1000")
        self.bench_n.setMaximumWidth(80)
        bench_row.addWidget(self.bench_n)
        self.bench_k = QLineEdit("10")
        self.bench_k.setMaximumWidth(60)
        bench_row.addWidget(QLabel("k:"))
        bench_row.addWidget(self.bench_k)
        self.bench_strategy = QComboBox()
        self.bench_strategy.addItems(["broadcast", "round_robin", "least_loaded"])
        bench_row.addWidget(self.bench_strategy)
        bench_btn = QPushButton("▶ Run Benchmark")
        bench_btn.setProperty("class", "primary")
        bench_row.addWidget(bench_btn)
        bench_row.addStretch()
        layout.addLayout(bench_row)

    def _on_refresh(self):
        self.signals.status_message.emit("Refreshing cluster status...")

    def _on_reset(self):
        self.signals.status_message.emit("Resetting cluster...")

    def get_params(self) -> list[dict]:
        return [
            {"name": "strategy", "label": "Routing Strategy", "type": "combo",
             "options": ["broadcast", "round_robin", "least_loaded"]},
            {"name": "sharding", "label": "Sharding Strategy", "type": "combo",
             "options": ["hash", "cluster", "geo"]},
        ]
