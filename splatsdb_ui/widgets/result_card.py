# SPDX-License-Identifier: GPL-3.0
"""Result card widget — displays a single search result."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

from splatsdb_ui.utils.api_client import SearchResult


class ResultCard(QFrame):
    """A card displaying one search result with score, text preview, and actions."""

    copy_requested = Signal(str)    # text
    store_requested = Signal(str)   # text
    explore_requested = Signal(int) # index

    def __init__(self, result: SearchResult, rank: int = 1):
        super().__init__()
        self.result = result
        self._build_ui(rank)

        self.setStyleSheet("""
            ResultCard {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 12px;
            }
            ResultCard:hover {
                border-color: #f9a825;
                background-color: #1e1e2e;
            }
        """)

    def _build_ui(self, rank: int):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # Top row: rank + score + actions
        top = QHBoxLayout()

        rank_label = QLabel(f"#{rank}")
        rank_label.setFont(QFont("", 12, QFont.Bold))
        rank_label.setStyleSheet("color: #f9a825;")
        rank_label.setFixedWidth(40)
        top.addWidget(rank_label)

        # Score badge
        score = self.result.score
        if score > 0.8:
            score_color = "#a6e3a1"
        elif score > 0.5:
            score_color = "#f9e2af"
        else:
            score_color = "#f38ba8"

        score_label = QLabel(f"{score:.4f}")
        score_label.setFont(QFont("", 11, QFont.Bold))
        score_label.setStyleSheet(f"color: {score_color};")
        score_label.setFixedWidth(70)
        top.addWidget(score_label)

        top.addStretch()

        # Action buttons
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(28, 28)
        copy_btn.setToolTip("Copy text")
        top.addWidget(copy_btn)

        explore_btn = QPushButton("🔗")
        explore_btn.setFixedSize(28, 28)
        explore_btn.setToolTip("Find similar")
        top.addWidget(explore_btn)

        layout.addLayout(top)

        # Text preview
        text = self.result.text or self.result.metadata or f"Vector #{self.result.index}"
        if len(text) > 300:
            text = text[:300] + "..."
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #cdd6f4;")
        layout.addWidget(text_label)

        # Metadata
        if self.result.metadata:
            meta_label = QLabel(self.result.metadata[:150])
            meta_label.setWordWrap(True)
            meta_label.setStyleSheet("color: #585b70; font-size: 11px;")
            layout.addWidget(meta_label)
