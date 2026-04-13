# SPDX-License-Identifier: GPL-3.0
"""Spatial view — Wing/Room/Hall memory navigator."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QComboBox,
    QGroupBox, QHeaderView, QSplitter,
)
from PySide6.QtCore import Qt

from splatsdb_ui.utils.signals import SignalBus
from splatsdb_ui.utils.state import AppState


class SpatialView(QWidget):
    """Spatial memory navigator — Wing (project) / Room (cluster) / Hall (type)."""

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
        title = QLabel("Spatial Memory")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()

        info_btn = QPushButton("🗺️ Structure Info")
        info_btn.clicked.connect(self._on_info)
        header.addWidget(info_btn)

        layout.addLayout(header)

        # Filter row
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Wing:"))
        self.wing_filter = QComboBox()
        self.wing_filter.setEditable(True)
        self.wing_filter.setPlaceholderText("Project / Domain")
        filter_row.addWidget(self.wing_filter)

        filter_row.addWidget(QLabel("Room:"))
        self.room_filter = QComboBox()
        self.room_filter.setEditable(True)
        self.room_filter.setPlaceholderText("Semantic Cluster")
        filter_row.addWidget(self.room_filter)

        filter_row.addWidget(QLabel("Hall:"))
        self.hall_filter = QComboBox()
        self.hall_filter.setEditable(True)
        self.hall_filter.addItems(["", "fact", "decision", "event", "error"])
        self.hall_filter.setPlaceholderText("Memory Type")
        filter_row.addWidget(self.hall_filter)

        search_btn = QPushButton("🔍 Filter")
        search_btn.setProperty("class", "primary")
        search_btn.clicked.connect(self._on_filter)
        filter_row.addWidget(search_btn)

        layout.addLayout(filter_row)

        # Spatial tree
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, stretch=1)

        # Wing tree (left)
        self.wing_tree = QTreeWidget()
        self.wing_tree.setHeaderLabels(["Wing", "Rooms", "Memories"])
        self.wing_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        splitter.addWidget(self.wing_tree)

        # Memory list (right)
        self.memory_tree = QTreeWidget()
        self.memory_tree.setHeaderLabels(["ID", "Text Preview", "Hall", "Score"])
        self.memory_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        splitter.addWidget(self.memory_tree)

        splitter.setSizes([350, 650])

    def _on_info(self):
        self.signals.status_message.emit("Loading spatial structure...")

    def _on_filter(self):
        wing = self.wing_filter.currentText()
        room = self.room_filter.currentText()
        hall = self.hall_filter.currentText()
        self.signals.status_message.emit(f"Spatial filter: wing={wing}, room={room}, hall={hall}")

    def get_params(self) -> list[dict]:
        return [
            {"name": "k", "label": "Top K", "type": "spin", "min": 1, "max": 1000, "default": 10},
        ]
