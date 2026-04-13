# SPDX-License-Identifier: GPL-3.0
"""Search view — vector similarity search."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QComboBox, QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import SEARCH, COLLECTION
from splatsdb_ui.widgets.result_card import ResultCard


class SearchView(QWidget):
    def __init__(self, signals, state):
        super().__init__()
        self.signals = signals
        self.state = state
        self._results = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Search")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 18px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Controls row
        controls = QHBoxLayout()
        controls.setSpacing(10)

        # Query input
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search query...")
        self.query_input.setMinimumHeight(40)
        self.query_input.setFont(QFont("", 13))
        self.query_input.returnPressed.connect(self._on_search)
        controls.addWidget(self.query_input, stretch=1)

        # Top-K
        controls.addWidget(QLabel("Top K:"))
        self.top_k = QSpinBox()
        self.top_k.setRange(1, 1000)
        self.top_k.setValue(10)
        self.top_k.setFixedWidth(70)
        controls.addWidget(self.top_k)

        # Collection
        controls.addWidget(QLabel(f"{COLLECTION}"))
        self.collection_combo = QComboBox()
        self.collection_combo.setMinimumWidth(160)
        controls.addWidget(self.collection_combo)

        # Search button
        search_btn = QPushButton(f"{SEARCH} Search")
        search_btn.setProperty("class", "primary")
        search_btn.clicked.connect(self._on_search)
        controls.addWidget(search_btn)

        layout.addLayout(controls)

        # Results area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(8)
        self.scroll.setWidget(self.results_widget)

        layout.addWidget(self.scroll, stretch=1)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _on_search(self):
        query = self.query_input.text().strip()
        if not query:
            return
        self.status_label.setText(f"Searching: {query}...")
        self.status_label.setStyleSheet(f"color: {Colors.WARNING}; font-size: 11px;")
        self.signals.search_requested.emit(query)

    def execute_search(self, query: str):
        self.query_input.setText(query)
        self._on_search()

    def show_results(self, results: list):
        # Clear old results
        for child in self.results_layout.children():
            child.widget().deleteLater()

        for i, r in enumerate(results):
            card = ResultCard(index=i, score=r.get("score", 0), metadata=r.get("text", ""))
            self.results_layout.addWidget(card)

        self.status_label.setText(f"{len(results)} results")
        self.status_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")

    def get_params(self) -> list:
        return [
            {"name": "top_k", "label": "Top K", "type": "spin", "min": 1, "max": 1000, "default": 10},
            {"name": "threshold", "label": "Min Score", "type": "float", "min": 0.0, "max": 1.0, "step": 0.01, "default": 0.0},
        ]
