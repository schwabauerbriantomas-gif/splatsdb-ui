# SPDX-License-Identifier: GPL-3.0
"""Dark theme loader — QSS stylesheet."""

from pathlib import Path
from PySide6.QtWidgets import QApplication


THEMES_DIR = Path(__file__).parent.parent / "resources" / "themes"


DARK_QSS = """
/* ═══════════════════════════════════════════════════════════════
   SplatsDB Dark Theme — Amber/Gold accent on #1e1e2e base
   ═══════════════════════════════════════════════════════════════ */

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

/* ── Window chrome ────────────────────────────────────────────── */
QMainWindow {
    background-color: #1e1e2e;
}
QMenuBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 2px;
}
QMenuBar::item {
    padding: 4px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #313244;
}
QMenu {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #f9a825;
    color: #1e1e2e;
}

/* ── Tooltips ─────────────────────────────────────────────────── */
QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
}

/* ── Input widgets ────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #cdd6f4;
    selection-background-color: #f9a825;
    selection-color: #1e1e2e;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #f9a825;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    selection-background-color: #f9a825;
    selection-color: #1e1e2e;
}

/* ── Buttons ──────────────────────────────────────────────────── */
QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 16px;
    color: #cdd6f4;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #45475a;
    border-color: #f9a825;
}
QPushButton:pressed {
    background-color: #f9a825;
    color: #1e1e2e;
}
QPushButton:disabled {
    background-color: #1e1e2e;
    color: #585b70;
    border-color: #313244;
}
QPushButton[class="primary"] {
    background-color: #f9a825;
    color: #1e1e2e;
    border-color: #f9a825;
}
QPushButton[class="primary"]:hover {
    background-color: #fbc02d;
}
QPushButton[class="danger"] {
    background-color: #f38ba8;
    color: #1e1e2e;
    border-color: #f38ba8;
}

/* ── Splitters ────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #313244;
}
QSplitter::handle:horizontal {
    width: 2px;
}
QSplitter::handle:vertical {
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #f9a825;
}

/* ── Scrollbars ───────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 5px;
    min-width: 30px;
}

/* ── Tab widget ───────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #313244;
    border-radius: 6px;
    background-color: #1e1e2e;
}
QTabBar::tab {
    background-color: #181825;
    border: 1px solid #313244;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 2px;
    color: #a6adc8;
}
QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #f9a825;
    border-bottom: 2px solid #f9a825;
}
QTabBar::tab:hover:!selected {
    background-color: #313244;
    color: #cdd6f4;
}

/* ── Tree/List views ──────────────────────────────────────────── */
QTreeWidget, QListView, QTableView {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    alternate-background-color: #1e1e2e;
    selection-background-color: #f9a825;
    selection-color: #1e1e2e;
}
QTreeWidget::item, QListView::item {
    padding: 4px 2px;
    border-bottom: 1px solid #1e1e2e;
}
QTreeWidget::item:hover, QListView::item:hover {
    background-color: #313244;
}

/* ── Progress bar ─────────────────────────────────────────────── */
QProgressBar {
    background-color: #313244;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #f9a825;
    border-radius: 4px;
}

/* ── Group boxes ──────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #f9a825;
}

/* ── Labels ───────────────────────────────────────────────────── */
QLabel[class="title"] {
    font-size: 18px;
    font-weight: 700;
    color: #f9a825;
}
QLabel[class="subtitle"] {
    font-size: 14px;
    color: #a6adc8;
}
QLabel[class="metric"] {
    font-size: 22px;
    font-weight: 700;
    color: #a6e3a1;
}

/* ── Status bar ───────────────────────────────────────────────── */
QStatusBar {
    background-color: #181825;
    border-top: 1px solid #313244;
    color: #a6adc8;
    font-size: 12px;
}

/* ── Sliders / spin boxes ─────────────────────────────────────── */
QSlider::groove:horizontal {
    background: #313244;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #f9a825;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSpinBox, QDoubleSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    color: #cdd6f4;
}

/* ── Checkboxes ───────────────────────────────────────────────── */
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 2px solid #45475a;
}
QCheckBox::indicator:checked {
    background-color: #f9a825;
    border-color: #f9a825;
}
QCheckBox::indicator:hover {
    border-color: #f9a825;
}
"""


def load_theme(app: QApplication, theme_name: str = "dark"):
    """Apply a QSS theme to the application."""
    app.setStyleSheet(DARK_QSS)
