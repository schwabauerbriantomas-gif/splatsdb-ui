# SPDX-License-Identifier: GPL-3.0
"""Result card — search result display."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
from PySide6.QtCore import Signal
from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import LINK, ARROW_R, TEXT, CHECK


class ResultCard(QFrame):
    store_clicked = Signal(int)
    explore_clicked = Signal(int)

    def __init__(self, index: int, score: float, metadata: str = ""):
        super().__init__()
        self.index = index
        self.score = score
        self.metadata = metadata
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"""
            ResultCard {{
                background-color: {Colors.BG_RAISED};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 14px;
            }}
            ResultCard:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 10, 12, 10)

        # Header row
        header = QHBoxLayout()
        idx_label = QLabel(f"#{self.index}")
        idx_label.setStyleSheet(f"color: {Colors.ACCENT}; font-weight: 700; font-size: 12px;")
        header.addWidget(idx_label)

        score_pct = f"{self.score:.1%}"
        score_label = QLabel(score_pct)
        score_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px; font-weight: 600;")
        header.addWidget(score_label)
        header.addStretch()

        # Action buttons (small)
        store_btn = QPushButton(TEXT)
        store_btn.setFixedSize(24, 24)
        store_btn.setToolTip("Store")
        store_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {Colors.TEXT_DIM}; font-size: 12px;
            }}
            QPushButton:hover {{ color: {Colors.ACCENT}; }}
        """)
        store_btn.clicked.connect(lambda: self.store_clicked.emit(self.index))
        header.addWidget(store_btn)

        link_btn = QPushButton(LINK)
        link_btn.setFixedSize(24, 24)
        link_btn.setToolTip("Explore")
        link_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {Colors.TEXT_DIM}; font-size: 12px;
            }}
            QPushButton:hover {{ color: {Colors.ACCENT}; }}
        """)
        link_btn.clicked.connect(lambda: self.explore_clicked.emit(self.index))
        header.addWidget(link_btn)

        layout.addLayout(header)

        # Score bar
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(self.score * 100))
        bar.setFixedHeight(4)
        bar.setTextVisible(False)
        layout.addWidget(bar)

        # Metadata preview
        if self.metadata:
            preview = QLabel(str(self.metadata)[:200])
            preview.setWordWrap(True)
            preview.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 12px;")
            layout.addWidget(preview)
