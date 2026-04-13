# SPDX-License-Identifier: GPL-3.0
"""Search view — semantic vector search with real-time results."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QComboBox, QScrollArea, QFrame,
    QSizePolicy, QGroupBox, QTextEdit,
)
from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtGui import QFont

from splatsdb_ui.utils.signals import SignalBus
from splatsdb_ui.utils.state import AppState
from splatsdb_ui.utils.api_client import SearchResult
from splatsdb_ui.workers.search_worker import SearchWorker
from splatsdb_ui.workers.embedding_worker import EmbeddingWorker
from splatsdb_ui.widgets.result_card import ResultCard


class SearchView(QWidget):
    """Main search view — query input + results list + filters."""

    def __init__(self, signals: SignalBus, state: AppState):
        super().__init__()
        self.signals = signals
        self.state = state
        self._search_thread = None
        self._embed_thread = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Search input row ────────────────────────────────────────
        input_row = QHBoxLayout()

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search query...")
        self.query_input.set MinimumHeight(44)
        self.query_input.setFont(QFont("", 14))
        self.query_input.returnPressed.connect(self._on_search)
        input_row.addWidget(self.query_input, stretch=1)

        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setProperty("class", "primary")
        self.search_btn.setMinimumHeight(44)
        self.search_btn.clicked.connect(self._on_search)
        input_row.addWidget(self.search_btn)

        layout.addLayout(input_row)

        # ── Options row ─────────────────────────────────────────────
        options_row = QHBoxLayout()

        k_label = QLabel("Top K:")
        options_row.addWidget(k_label)

        self.k_spin = QSpinBox()
        self.k_spin.setRange(1, 1000)
        self.k_spin.setValue(10)
        options_row.addWidget(self.k_spin)

        model_label = QLabel("Model:")
        options_row.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        self.model_combo.addItem("Default (SimCos)")
        self.model_combo.addItem("llama-embed-nemotron-8b")
        self.model_combo.addItem("all-MiniLM-L6-v2")
        options_row.addWidget(self.model_combo)

        self.advanced_btn = QPushButton("Advanced ▼")
        self.advanced_btn.setCheckable(True)
        options_row.addWidget(self.advanced_btn)

        options_row.addStretch()

        self.results_count = QLabel("")
        self.results_count.setStyleSheet("color: #a6adc8;")
        options_row.addWidget(self.results_count)

        layout.addLayout(options_row)

        # ── Advanced options (collapsible) ──────────────────────────
        self.advanced_panel = QGroupBox("Advanced Options")
        self.advanced_panel.setVisible(False)
        adv_layout = QHBoxLayout(self.advanced_panel)

        adv_layout.addWidget(QLabel("Index:"))
        self.index_combo = QComboBox()
        self.index_combo.addItems(["Auto (Fused)", "HNSW", "LSH", "Quantized", "Graph", "Spatial"])
        adv_layout.addWidget(self.index_combo)

        adv_layout.addWidget(QLabel("Metric:"))
        self.metric_combo = QComboBox()
        self.metric_combo.addItems(["Cosine", "L2 (Euclidean)"])
        adv_layout.addWidget(self.metric_combo)

        self.spatial_wing = QLineEdit()
        self.spatial_wing.setPlaceholderText("Wing filter")
        adv_layout.addWidget(self.spatial_wing)

        self.spatial_room = QLineEdit()
        self.spatial_room.setPlaceholderText("Room filter")
        adv_layout.addWidget(self.spatial_room)

        self.advanced_btn.toggled.connect(self.advanced_panel.setVisible)
        layout.addWidget(self.advanced_panel)

        # ── Results area ────────────────────────────────────────────
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setFrameShape(QFrame.NoFrame)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(8)
        self.results_scroll.setWidget(self.results_container)

        layout.addWidget(self.results_scroll, stretch=1)

        # Empty state
        self._show_empty_state()

    def _show_empty_state(self):
        """Show placeholder when no results."""
        for child in self.results_layout.children():
            child.widget().deleteLater()

        empty = QLabel("Enter a query and press Search or Enter")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet("color: #585b70; font-size: 16px; padding: 60px;")
        self.results_layout.addWidget(empty)

    def execute_search(self, query: str):
        """Called from MainWindow when global search triggers."""
        self.query_input.setText(query)
        self._on_search()

    def _on_search(self):
        """Execute the search."""
        query = self.query_input.text().strip()
        if not query:
            return

        self.search_btn.setEnabled(False)
        self.search_btn.setText("⏳ Searching...")
        self.results_count.setText("Searching...")

        # Clear previous results
        for child in self.results_layout.children():
            child.widget().deleteLater()

        # Start search worker
        self._search_thread = QThread()
        self._search_worker = SearchWorker(
            query=query,
            top_k=self.k_spin.value(),
            client_url=self.state.connection.url,
            api_key=self.state.connection.api_key,
        )
        self._search_worker.moveToThread(self._search_thread)
        self._search_thread.started.connect(self._search_worker.run)
        self._search_worker.finished.connect(self._on_search_finished)
        self._search_worker.finished.connect(self._search_thread.quit)
        self._search_thread.start()

    @Slot(list)
    def _on_search_finished(self, results: list[SearchResult]):
        """Display search results."""
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍 Search")

        # Clear
        for child in self.results_layout.children():
            child.widget().deleteLater()

        if not results:
            empty = QLabel("No results found")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #585b70; font-size: 16px; padding: 60px;")
            self.results_layout.addWidget(empty)
            self.results_count.setText("0 results")
            return

        self.results_count.setText(f"{len(results)} results")
        for i, result in enumerate(results):
            card = ResultCard(result, rank=i + 1)
            self.results_layout.addWidget(card)

    def get_params(self) -> list[dict]:
        """Return parameter definitions for the param panel."""
        return [
            {"name": "top_k", "label": "Top K", "type": "spin", "min": 1, "max": 1000, "default": 10},
            {"name": "model", "label": "Embedding Model", "type": "combo",
             "options": ["Default", "nemotron-8b", "MiniLM-L6", "BGE-Small"]},
            {"name": "index", "label": "Search Index", "type": "combo",
             "options": ["Auto", "HNSW", "LSH", "Quantized", "Graph", "Spatial"]},
        ]
