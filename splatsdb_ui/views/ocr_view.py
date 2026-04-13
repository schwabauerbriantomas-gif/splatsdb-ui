# SPDX-License-Identifier: GPL-3.0
"""OCR view — image/PDF to searchable text pipeline."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QProgressBar, QTextEdit, QSplitter,
    QFrame, QFileDialog,
)
from PySide6.QtCore import Qt
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import OCR, SEARCH, FILE, REFRESH


class OCRView(QWidget):
    def __init__(self, signals, state):
        super().__init__()
        self.signals = signals
        self.state = state
        self._current_file = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("OCR Pipeline")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 18px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # File input
        file_row = QHBoxLayout()
        self.file_label = QLineEdit()
        self.file_label.setPlaceholderText("Select image or PDF...")
        self.file_label.setReadOnly(True)
        file_row.addWidget(self.file_label, stretch=1)

        browse_btn = QPushButton(f"{FILE} Browse")
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        # Options row
        options = QHBoxLayout()
        options.addWidget(QLabel("Engine:"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Tesseract", "PaddleOCR"])
        options.addWidget(self.engine_combo)

        options.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["spa", "eng", "por", "fra", "deu"])
        self.lang_combo.setCurrentText("spa")
        options.addWidget(self.lang_combo)

        run_btn = QPushButton(f"{SEARCH} Extract Text")
        run_btn.setProperty("class", "primary")
        options.addWidget(run_btn)

        options.addStretch()
        layout.addLayout(options)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        # Splitter: preview | text output
        splitter = QSplitter(Qt.Horizontal)

        # Preview
        preview_frame = QFrame()
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_label = QLabel("No file loaded")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        preview_layout.addWidget(self.preview_label)
        splitter.addWidget(preview_frame)

        # Text output
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setPlaceholderText("Extracted text will appear here...")
        splitter.addWidget(self.text_output)

        splitter.setSizes([400, 600])
        layout.addWidget(splitter, stretch=1)

        # Bottom actions
        actions = QHBoxLayout()
        embed_btn = QPushButton("Embed & Store")
        embed_btn.setProperty("class", "primary")
        actions.addWidget(embed_btn)
        actions.addWidget(QPushButton("Copy Text"))
        actions.addStretch()
        layout.addLayout(actions)

    def _browse_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files", "",
            "Images (*.png *.jpg *.jpeg *.tiff *.bmp);;PDF (*.pdf);;All (*)"
        )
        if files:
            self.file_label.setText(files[0])
            self._current_file = files[0]

    def get_params(self) -> list:
        return [
            {"name": "ocr_engine", "label": "Engine", "type": "combo", "options": ["tesseract", "paddleocr"], "default": "tesseract"},
            {"name": "ocr_lang", "label": "Language", "type": "combo", "options": ["spa", "eng", "por", "fra", "deu"], "default": "spa"},
            {"name": "auto_embed", "label": "Auto-embed", "type": "check", "default": True},
        ]
