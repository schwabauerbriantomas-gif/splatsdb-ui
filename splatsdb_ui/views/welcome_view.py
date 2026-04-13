# SPDX-License-Identifier: GPL-3.0
"""Welcome view — landing screen with drop zone + recent + model selector."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont

from splatsdb_ui.utils.signals import SignalBus
from splatsdb_ui.utils.state import AppState


class DropZone(QFrame):
    """Drag-and-drop zone for importing files (vectors, documents, images for OCR)."""
    files_dropped = Signal(list)  # list of file paths

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setObjectName("dropZone")
        self.setMinimumHeight(200)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("📂")
        icon.setFont(QFont("", 48))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("Drop files here")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Vectors (.bin, .fvecs) • Documents (.txt, .pdf, .json) • Images (.png, .jpg) for OCR"
        )
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.setStyleSheet("""
            #dropZone {
                border: 2px dashed #45475a;
                border-radius: 12px;
                background-color: #181825;
                padding: 40px;
            }
            #dropZone:hover {
                border-color: #f9a825;
                background-color: #1e1e2e;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                #dropZone {
                    border: 2px solid #f9a825;
                    border-radius: 12px;
                    background-color: #262637;
                    padding: 40px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            #dropZone {
                border: 2px dashed #45475a;
                border-radius: 12px;
                background-color: #181825;
                padding: 40px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("""
            #dropZone {
                border: 2px dashed #45475a;
                border-radius: 12px;
                background-color: #181825;
                padding: 40px;
            }
        """)
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                files.append(path)
        if files:
            self.files_dropped.emit(files)


class WelcomeView(QWidget):
    """Welcome screen — first thing the user sees."""

    def __init__(self, signals: SignalBus, state: AppState):
        super().__init__()
        self.signals = signals
        self.state = state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(24)

        # Header
        header = QVBoxLayout()
        title = QLabel("SplatsDB")
        title.setProperty("class", "title")
        title.setFont(QFont("", 32, QFont.Bold))
        title.setStyleSheet("color: #f9a825; font-size: 32px; font-weight: 700;")
        header.addWidget(title)

        subtitle = QLabel("Gaussian Splat Vector Search Engine")
        subtitle.setProperty("class", "subtitle")
        subtitle.setStyleSheet("color: #a6adc8; font-size: 16px;")
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_zone, stretch=1)

        # Quick actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        actions = [
            ("🔍 Semantic Search", "Ctrl+K", lambda: self.signals.view_changed.emit("search")),
            ("📚 Collections", "Ctrl+3", lambda: self.signals.view_changed.emit("collections")),
            ("🔗 Knowledge Graph", "Ctrl+4", lambda: self.signals.view_changed.emit("graph")),
            ("🗺️ Spatial Memory", "Ctrl+5", lambda: self.signals.view_changed.emit("spatial")),
            ("📷 OCR + Embed", "Ctrl+8", lambda: self.signals.view_changed.emit("ocr")),
        ]

        for label, shortcut, callback in actions:
            btn = QPushButton(f"{label}\n{shortcut}")
            btn.setMinimumHeight(60)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)

        layout.addLayout(actions_layout)

        # Model selector row
        model_layout = QHBoxLayout()
        model_label = QLabel("Active embedding model:")
        model_label.setStyleSheet("color: #a6adc8;")
        model_layout.addWidget(model_label)

        self.model_btn = QPushButton("Select Model →")
        self.model_btn.clicked.connect(lambda: self.signals.view_changed.emit("settings"))
        model_layout.addWidget(self.model_btn)
        model_layout.addStretch()

        # Backend status
        self.status_label = QLabel("● Disconnected")
        self.status_label.setStyleSheet("color: #f38ba8;")
        model_layout.addWidget(self.status_label)

        layout.addLayout(model_layout)

    def _on_files_dropped(self, files: list[str]):
        """Handle dropped files — route by type."""
        for path in files:
            ext = path.rsplit(".", 1)[-1].lower()
            if ext in ("png", "jpg", "jpeg", "tiff", "bmp", "pdf"):
                # Route to OCR view
                self.signals.view_changed.emit("ocr")
                self.signals.status_message.emit(f"OCR: {path}")
            elif ext in ("bin", "fvecs", "bvecs", "ivecs"):
                # Route to collections (vector import)
                self.signals.view_changed.emit("collections")
                self.signals.status_message.emit(f"Import vectors: {path}")
            elif ext in ("txt", "json", "md", "csv"):
                # Route to search (document store)
                self.signals.view_changed.emit("search")
                self.signals.status_message.emit(f"Document: {path}")

    def update_connection_status(self, connected: bool, version: str = ""):
        if connected:
            self.status_label.setText(f"● Connected v{version}")
            self.status_label.setStyleSheet("color: #a6e3a1;")
        else:
            self.status_label.setText("● Disconnected")
            self.status_label.setStyleSheet("color: #f38ba8;")
