# SPDX-License-Identifier: GPL-3.0
"""Collections view — browse and manage vector collections."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QFileDialog,
    QGroupBox, QProgressBar,
)
from PySide6.QtCore import Qt, Signal

from splatsdb_ui.utils.signals import SignalBus
from splatsdb_ui.utils.state import AppState


class CollectionsView(QWidget):
    """Collection browser — list collections, shards, document counts."""

    def __init__(self, signals: SignalBus, state: AppState):
        super().__init__()
        self.signals = signals
        self.state = state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header row
        header = QHBoxLayout()

        title = QLabel("Collections")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()

        import_btn = QPushButton("📥 Import Vectors")
        import_btn.setProperty("class", "primary")
        import_btn.clicked.connect(self._on_import)
        header.addWidget(import_btn)

        add_doc_btn = QPushButton("📄 Add Document")
        add_doc_btn.clicked.connect(self._on_add_doc)
        header.addWidget(add_doc_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._on_refresh)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Stats bar
        self.stats_label = QLabel("No collections loaded")
        self.stats_label.setStyleSheet("color: #a6adc8; padding: 8px;")
        layout.addWidget(self.stats_label)

        # Collection tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "Collection", "Vectors", "Dimension", "Backend",
            "HNSW", "LSH", "Quantized", "Size"
        ])
        self.tree.setAlternatingRowColors(True)
        header_item = self.tree.headerItem()
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        layout.addWidget(self.tree, stretch=1)

        # Import progress
        self.progress_group = QGroupBox("Import Progress")
        self.progress_group.setVisible(False)
        prog_layout = QVBoxLayout(self.progress_group)
        self.progress_bar = QProgressBar()
        prog_layout.addWidget(self.progress_bar)
        self.progress_label = QLabel("")
        prog_layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_group)

    def _on_import(self):
        """Open file dialog to import vectors."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Import Vectors", "",
            "Vector Files (*.bin *.fvecs *.bvecs *.ivecs);;All Files (*)"
        )
        if files:
            self.signals.status_message.emit(f"Importing {len(files)} file(s)...")
            self.signals.view_changed.emit("collections")

    def _on_add_doc(self):
        """Add a document manually."""
        self.signals.status_message.emit("Add document dialog...")

    def _on_refresh(self):
        """Refresh collection list from backend."""
        self.signals.status_message.emit("Refreshing collections...")

    def get_params(self) -> list[dict]:
        return [
            {"name": "dim", "label": "Dimension", "type": "spin", "min": 1, "max": 8192, "default": 64},
            {"name": "max_splats", "label": "Max Splats", "type": "spin", "min": 1000, "max": 10000000, "default": 100000},
            {"name": "backend", "label": "Storage Backend", "type": "combo", "options": ["sqlite", "json"]},
        ]
