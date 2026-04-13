# SPDX-License-Identifier: GPL-3.0
"""Status bar widget — GPU VRAM, connection, model info."""

from PySide6.QtWidgets import QStatusBar, QLabel, QProgressBar, QHBoxLayout, QWidget
from PySide6.QtCore import Qt


class SplatsDBStatusBar(QStatusBar):
    """Custom status bar with GPU monitor, model name, and connection indicator."""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        # Connection indicator
        self.conn_label = QLabel("● Disconnected")
        self.conn_label.setStyleSheet("color: #f38ba8; padding: 0 12px;")
        self.addWidget(self.conn_label)

        # Separator
        self.addWidget(self._separator())

        # Active model
        self.model_label = QLabel("Model: none")
        self.model_label.setStyleSheet("color: #a6adc8; padding: 0 12px;")
        self.addWidget(self.model_label)

        # Separator
        self.addWidget(self._separator())

        # GPU VRAM
        self.vram_label = QLabel("GPU: —")
        self.vram_label.setStyleSheet("color: #a6adc8; padding: 0 12px;")
        self.addWidget(self.vram_label)

        self.vram_bar = QProgressBar()
        self.vram_bar.setFixedWidth(120)
        self.vram_bar.setFixedHeight(8)
        self.vram_bar.setTextVisible(False)
        self.vram_bar.setStyleSheet("""
            QProgressBar { background-color: #313244; border: none; border-radius: 4px; }
            QProgressBar::chunk { background-color: #a6e3a1; border-radius: 4px; }
        """)
        self.addPermanentWidget(self.vram_bar)

        # Permanent message area
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: #585b70; padding: 0 12px;")
        self.addPermanentWidget(self.message_label)

    def _separator(self) -> QLabel:
        sep = QLabel("│")
        sep.setStyleSheet("color: #313244;")
        return sep

    def show_message(self, text: str):
        self.message_label.setText(text)

    def set_connected(self, connected: bool, version: str = ""):
        if connected:
            self.conn_label.setText(f"● Connected v{version}")
            self.conn_label.setStyleSheet("color: #a6e3a1; padding: 0 12px;")
        else:
            self.conn_label.setText("● Disconnected")
            self.conn_label.setStyleSheet("color: #f38ba8; padding: 0 12px;")

    def set_model(self, name: str):
        self.model_label.setText(f"Model: {name}")

    def set_vram(self, used_gb: float, total_gb: float):
        self.vram_label.setText(f"GPU: {used_gb:.1f}/{total_gb:.1f} GB")
        pct = int((used_gb / total_gb) * 100) if total_gb > 0 else 0
        self.vram_bar.setValue(pct)
        # Color based on usage
        if pct > 90:
            color = "#f38ba8"
        elif pct > 70:
            color = "#f9e2af"
        else:
            color = "#a6e3a1"
        self.vram_bar.setStyleSheet(f"""
            QProgressBar {{ background-color: #313244; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}
        """)
