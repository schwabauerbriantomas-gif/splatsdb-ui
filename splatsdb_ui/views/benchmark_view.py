# SPDX-License-Identifier: GPL-3.0
"""Benchmark view — GPU/CPU benchmarking with results."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QSpinBox, QComboBox, QLineEdit, QTextEdit,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt

from splatsdb_ui.utils.signals import SignalBus
from splatsdb_ui.utils.state import AppState


class BenchmarkView(QWidget):
    """Benchmark runner — GPU vs CPU, HNSW recall, ingestion benchmarks."""

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
        title = QLabel("Benchmarks")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()

        gpu_btn = QPushButton("🖥️ GPU Info")
        gpu_btn.clicked.connect(self._on_gpu_info)
        header.addWidget(gpu_btn)

        layout.addLayout(header)

        # Tabs for different benchmark types
        tabs = QTabWidget()
        layout.addWidget(tabs, stretch=1)

        # Tab 1: GPU Search Benchmark
        gpu_tab = QWidget()
        gpu_layout = QVBoxLayout(gpu_tab)
        params = QGroupBox("GPU Search Benchmark Parameters")
        params_layout = QHBoxLayout(params)
        
        params_layout.addWidget(QLabel("Vectors:"))
        self.gpu_n = QSpinBox()
        self.gpu_n.setRange(1000, 10000000)
        self.gpu_n.setValue(10000)
        self.gpu_n.setSingleStep(1000)
        params_layout.addWidget(self.gpu_n)
        
        params_layout.addWidget(QLabel("Dim:"))
        self.gpu_dim = QSpinBox()
        self.gpu_dim.setRange(1, 8192)
        self.gpu_dim.setValue(640)
        params_layout.addWidget(self.gpu_dim)
        
        params_layout.addWidget(QLabel("Queries:"))
        self.gpu_q = QSpinBox()
        self.gpu_q.setRange(1, 100000)
        self.gpu_q.setValue(100)
        params_layout.addWidget(self.gpu_q)
        
        params_layout.addWidget(QLabel("Metric:"))
        self.gpu_metric = QComboBox()
        self.gpu_metric.addItems(["l2", "cosine"])
        params_layout.addWidget(self.gpu_metric)
        
        run_btn = QPushButton("▶ Run")
        run_btn.setProperty("class", "primary")
        params_layout.addWidget(run_btn)
        
        gpu_layout.addWidget(params)
        gpu_layout.addWidget(QTextEdit())
        tabs.addTab(gpu_tab, "GPU Search")

        # Tab 2: HNSW Recall Benchmark
        hnsw_tab = QWidget()
        hnsw_layout = QVBoxLayout(hnsw_tab)
        hnsw_params = QGroupBox("HNSW Benchmark")
        hnsw_pl = QHBoxLayout(hnsw_params)
        
        hnsw_pl.addWidget(QLabel("Train:"))
        hnsw_pl.addWidget(QLineEdit("(binary file)"))
        hnsw_pl.addWidget(QLabel("Queries:"))
        hnsw_pl.addWidget(QLineEdit("(binary file)"))
        hnsw_pl.addWidget(QLabel("Dim:"))
        hnsw_pl.addWidget(QSpinBox())
        
        hnsw_run = QPushButton("▶ Run")
        hnsw_run.setProperty("class", "primary")
        hnsw_pl.addWidget(hnsw_run)
        
        hnsw_layout.addWidget(hnsw_params)
        hnsw_layout.addWidget(QTextEdit())
        tabs.addTab(hnsw_tab, "HNSW Recall")

        # Tab 3: GPU Ingest Pipeline
        ingest_tab = QWidget()
        ingest_layout = QVBoxLayout(ingest_tab)
        ingest_params = QGroupBox("GPU Ingest Pipeline")
        ingest_pl = QHBoxLayout(ingest_params)
        
        ingest_pl.addWidget(QLabel("Vectors:"))
        self.ingest_n = QSpinBox()
        self.ingest_n.setRange(1000, 10000000)
        self.ingest_n.setValue(100000)
        ingest_pl.addWidget(self.ingest_n)
        
        ingest_pl.addWidget(QLabel("Dim:"))
        self.ingest_dim = QSpinBox()
        self.ingest_dim.setValue(640)
        ingest_pl.addWidget(self.ingest_dim)
        
        ingest_pl.addWidget(QLabel("Clusters:"))
        self.ingest_clusters = QSpinBox()
        self.ingest_clusters.setValue(100)
        ingest_pl.addWidget(self.ingest_clusters)
        
        ingest_run = QPushButton("▶ Run")
        ingest_run.setProperty("class", "primary")
        ingest_pl.addWidget(ingest_run)
        
        ingest_layout.addWidget(ingest_params)
        ingest_layout.addWidget(QTextEdit())
        tabs.addTab(ingest_tab, "GPU Ingest")

        # Tab 4: Results
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Benchmark", "Vectors", "Dim", "QPS", "Latency (ms)", "Recall"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        results_layout.addWidget(self.results_table)
        tabs.addTab(results_tab, "Results History")

    def _on_gpu_info(self):
        self.signals.status_message.emit("Querying GPU info...")

    def get_params(self) -> list[dict]:
        return []
