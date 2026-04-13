# SPDX-License-Identifier: GPL-3.0
"""Cluster view — distributed cluster dashboard."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QFormLayout, QLineEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import CLUSTER, REFRESH, ADD, REMOVE


class ClusterView(QWidget):
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
        title = QLabel("Cluster")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 18px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton(f"{REFRESH}")
        refresh_btn.setFixedSize(32, 32)
        header.addWidget(refresh_btn)
        add_btn = QPushButton(f"{ADD} Node")
        add_btn.setProperty("class", "primary")
        header.addWidget(add_btn)
        layout.addLayout(header)

        # Cluster info
        info_group = QGroupBox("Cluster Status")
        info_form = QFormLayout(info_group)
        self.lbl_nodes = QLabel("0 nodes")
        self.lbl_shards = QLabel("0 shards")
        self.lbl_status = QLabel("Standby")
        info_form.addRow("Nodes:", self.lbl_nodes)
        info_form.addRow("Shards:", self.lbl_shards)
        info_form.addRow("Status:", self.lbl_status)
        layout.addWidget(info_group)

        # Node table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Node", "Address", "Status", "Vectors", "CPU", "Memory"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, stretch=1)

        # Routing info
        routing = QHBoxLayout()
        routing.addWidget(QLabel("Sharding:"))
        self.shard_input = QLineEdit()
        self.shard_input.setPlaceholderText("Number of shards")
        routing.addWidget(self.shard_input)
        routing.addStretch()
        layout.addLayout(routing)

    def get_params(self) -> list:
        return [
            {"name": "min_nodes", "label": "Min Nodes", "type": "spin", "min": 1, "max": 100, "default": 1},
            {"name": "max_nodes", "label": "Max Nodes", "type": "spin", "min": 1, "max": 1000, "default": 50},
            {"name": "n_chunks", "label": "MapReduce Chunks", "type": "spin", "min": 1, "max": 256, "default": 32},
        ]
