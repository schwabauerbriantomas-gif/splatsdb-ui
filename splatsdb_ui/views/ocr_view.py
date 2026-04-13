# SPDX-License-Identifier: GPL-3.0
"""OCR view — extract text from images/PDFs → embed → search."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QComboBox, QGroupBox, QProgressBar,
    QSplitter, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QFont

from splatsdb_ui.utils.signals import SignalBus
from splatsdb_ui.utils.state import AppState
from splatsdb_ui.workers.ocr_worker import OCRWorker


class OCRView(QWidget):
    """OCR view — image/PDF → text extraction → embedding → store/search."""

    def __init__(self, signals: SignalBus, state: AppState):
        super().__init__()
        self.signals = signals
        self.state = state
        self._ocr_thread = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("OCR + Embed")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()

        # OCR engine selector
        header.addWidget(QLabel("Engine:"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Auto", "Tesseract", "PaddleOCR"])
        header.addWidget(self.engine_combo)

        # Language
        header.addWidget(QLabel("Lang:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["spa+eng", "eng", "spa", "por", "fra", "deu"])
        header.addWidget(self.lang_combo)

        layout.addLayout(header)

        # Main splitter: image preview | extracted text
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, stretch=1)

        # Left: Image/file preview
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(8)

        open_btn = QPushButton("📂 Open Image / PDF")
        open_btn.setProperty("class", "primary")
        open_btn.clicked.connect(self._on_open_file)
        left_layout.addWidget(open_btn)

        self.image_label = QLabel("No image loaded")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(300)
        self.image_label.setStyleSheet("""
            background-color: #181825;
            border: 1px solid #313244;
            border-radius: 8px;
            color: #585b70;
            padding: 20px;
        """)
        left_layout.addWidget(self.image_label, stretch=1)

        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        left_layout.addWidget(self.file_label)

        splitter.addWidget(left)

        # Right: Extracted text + actions
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(8)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        right_layout.addWidget(self.progress)

        # Extracted text
        text_group = QGroupBox("Extracted Text")
        text_layout = QVBoxLayout(text_group)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Open an image or PDF to extract text...\n\n"
            "Supports: PNG, JPG, TIFF, BMP, PDF\n"
            "Languages: Spanish, English, Portuguese, French, German"
        )
        text_layout.addWidget(self.text_edit)
        right_layout.addWidget(text_group, stretch=1)

        # Action buttons
        actions = QHBoxLayout()

        extract_btn = QPushButton("🔍 Extract Text")
        extract_btn.setProperty("class", "primary")
        extract_btn.clicked.connect(self._on_extract)
        actions.addWidget(extract_btn)

        embed_btn = QPushButton("🧠 Embed + Store")
        embed_btn.clicked.connect(self._on_embed_store)
        actions.addWidget(embed_btn)

        search_btn = QPushButton("🔎 Search Similar")
        search_btn.clicked.connect(self._on_search_similar)
        actions.addWidget(search_btn)

        copy_btn = QPushButton("📋 Copy Text")
        copy_btn.clicked.connect(self._on_copy)
        actions.addWidget(copy_btn)

        right_layout.addLayout(actions)
        splitter.addWidget(right)
        splitter.setSizes([450, 550])

        self._current_file = ""

    def _on_open_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Open Image or PDF", "",
            "Images (*.png *.jpg *.jpeg *.tiff *.bmp);;PDF (*.pdf);;All Files (*)"
        )
        if files:
            self._current_file = files[0]
            self.file_label.setText(self._current_file)

            # Show image preview
            if self._current_file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
                pixmap = QPixmap(self._current_file)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        self.image_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                    self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText("PDF file selected\n(preview not available)")

    def _on_extract(self):
        """Run OCR on the current file."""
        if not self._current_file:
            self.signals.status_message.emit("No file selected")
            return

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # Indeterminate

        self._ocr_thread = QThread()
        self._ocr_worker = OCRWorker(
            file_path=self._current_file,
            engine=self.engine_combo.currentText().lower(),
            language=self.lang_combo.currentText(),
        )
        self._ocr_worker.moveToThread(self._ocr_thread)
        self._ocr_thread.started.connect(self._ocr_worker.run)
        self._ocr_worker.finished.connect(self._on_ocr_finished)
        self._ocr_worker.finished.connect(self._ocr_thread.quit)
        self._ocr_thread.start()

    def _on_ocr_finished(self, text: str, error: str):
        """Handle OCR completion."""
        self.progress.setVisible(False)
        if error:
            self.text_edit.setPlainText(f"ERROR: {error}")
            self.signals.status_message.emit(f"OCR failed: {error}")
        else:
            self.text_edit.setPlainText(text)
            self.signals.status_message.emit(f"OCR complete: {len(text)} chars extracted")

    def _on_embed_store(self):
        """Embed the extracted text and store in SplatsDB."""
        text = self.text_edit.toPlainText()
        if not text:
            self.signals.status_message.emit("No text to embed")
            return
        self.signals.status_message.emit(f"Embedding + storing {len(text)} chars...")

    def _on_search_similar(self):
        """Search for similar documents using the extracted text."""
        text = self.text_edit.toPlainText()
        if not text:
            self.signals.status_message.emit("No text to search")
            return
        self.signals.search_requested.emit(text[:500])

    def _on_copy(self):
        """Copy extracted text to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        self.signals.status_message.emit("Text copied to clipboard")

    def get_params(self) -> list[dict]:
        return [
            {"name": "engine", "label": "OCR Engine", "type": "combo",
             "options": ["Auto", "Tesseract", "PaddleOCR"]},
            {"name": "language", "label": "Language", "type": "combo",
             "options": ["spa+eng", "eng", "spa", "por", "fra", "deu"]},
        ]
