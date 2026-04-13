# SPDX-License-Identifier: GPL-3.0
"""Dark theme — refined professional palette.

Base: deep blue-gray (not purple)
Accent: warm amber
Style: JetBrains / Linear / Vercel inspired
"""

DARK_QSS = """
/* ── Global ────────────────────────────────────────────────── */
QWidget {
    background-color: #0f1117;
    color: #d1d5db;
    font-family: "Inter", "Segoe UI", "SF Pro", sans-serif;
    font-size: 13px;
    selection-background-color: #f59e0b;
    selection-color: #0f1117;
}

QMainWindow {
    background-color: #0f1117;
}

/* ── Menu Bar ──────────────────────────────────────────────── */
QMenuBar {
    background-color: #161b22;
    border-bottom: 1px solid #21262d;
    padding: 2px 8px;
    font-size: 12px;
}
QMenuBar::item {
    padding: 4px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #21262d;
}
QMenu {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #f59e0b;
    color: #0f1117;
}
QMenu::separator {
    height: 1px;
    background: #21262d;
    margin: 4px 8px;
}

/* ── Tab Bar ───────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background-color: #0f1117;
}
QTabBar {
    background-color: #161b22;
    border-bottom: 1px solid #21262d;
}
QTabBar::tab {
    background-color: transparent;
    padding: 8px 16px;
    margin-right: 0px;
    color: #6b7280;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.3px;
}
QTabBar::tab:selected {
    color: #f59e0b;
    border-bottom: 2px solid #f59e0b;
}
QTabBar::tab:hover:!selected {
    color: #d1d5db;
    background-color: rgba(255,255,255,0.03);
}

/* ── Buttons ───────────────────────────────────────────────── */
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 14px;
    color: #d1d5db;
    font-weight: 500;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #484f58;
}
QPushButton:pressed {
    background-color: #161b22;
}
QPushButton[primary="true"],
QPushButton[class="primary"] {
    background-color: #f59e0b;
    border-color: #d97706;
    color: #0f1117;
    font-weight: 600;
}
QPushButton[primary="true"]:hover,
QPushButton[class="primary"]:hover {
    background-color: #fbbf24;
}
QPushButton[danger="true"] {
    background-color: #991b1b;
    border-color: #dc2626;
    color: #fca5a5;
}
QPushButton[danger="true"]:hover {
    background-color: #b91c1c;
}

/* ── Input ─────────────────────────────────────────────────── */
QLineEdit {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 6px 12px;
    color: #d1d5db;
    selection-background-color: #f59e0b;
    selection-color: #0f1117;
}
QLineEdit:focus {
    border-color: #f59e0b;
}

QTextEdit, QPlainTextEdit {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 8px;
    color: #d1d5db;
}

/* ── Spin / Combo ──────────────────────────────────────────── */
QSpinBox, QDoubleSpinBox {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 4px 8px;
    color: #d1d5db;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #f59e0b;
}
QSpinBox::up-button, QDoubleSpinBox::up-button {
    border: none;
    background: transparent;
    width: 20px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    border: none;
    background: transparent;
    width: 20px;
}

QComboBox {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 4px 12px;
    color: #d1d5db;
}
QComboBox:hover {
    border-color: #484f58;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #21262d;
    selection-background-color: #f59e0b;
    selection-color: #0f1117;
    outline: none;
}

/* ── Checkbox ──────────────────────────────────────────────── */
QCheckBox {
    spacing: 8px;
    color: #d1d5db;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #30363d;
    background-color: #161b22;
}
QCheckBox::indicator:checked {
    background-color: #f59e0b;
    border-color: #d97706;
}

/* ── Slider ────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    height: 4px;
    background: #21262d;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    background: #f59e0b;
    border-radius: 7px;
    margin: -5px 0;
}

/* ── Group Box ─────────────────────────────────────────────── */
QGroupBox {
    font-weight: 600;
    color: #9ca3af;
    border: 1px solid #21262d;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 8px 12px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #6b7280;
}

/* ── Scroll Area ───────────────────────────────────────────── */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: #21262d;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #30363d;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 2px 4px;
}
QScrollBar::handle:horizontal {
    background: #21262d;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #30363d;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Progress Bar ──────────────────────────────────────────── */
QProgressBar {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #f59e0b;
    border-radius: 3px;
}

/* ── Splitter ──────────────────────────────────────────────── */
QSplitter::handle {
    background: #21262d;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}

/* ── Tree / List ───────────────────────────────────────────── */
QTreeWidget, QListView {
    background-color: #0f1117;
    border: none;
    color: #d1d5db;
    outline: none;
}
QTreeWidget::item, QListView::item {
    padding: 4px 8px;
    border-radius: 4px;
}
QTreeWidget::item:selected, QListView::item:selected {
    background-color: rgba(245, 158, 11, 0.12);
    color: #f59e0b;
}
QTreeWidget::item:hover, QListView::item:hover {
    background-color: rgba(255,255,255,0.03);
}
QHeaderView::section {
    background-color: #161b22;
    border: none;
    border-bottom: 1px solid #21262d;
    padding: 6px 12px;
    color: #6b7280;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Status Bar ────────────────────────────────────────────── */
QStatusBar {
    background-color: #161b22;
    border-top: 1px solid #21262d;
    color: #6b7280;
    font-size: 11px;
    padding: 2px 8px;
}

/* ── Tooltip ───────────────────────────────────────────────── */
QToolTip {
    background-color: #161b22;
    border: 1px solid #30363d;
    color: #d1d5db;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}

/* ── Frame / Card ──────────────────────────────────────────── */
QFrame[class="card"] {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px;
}
"""

# Color palette constants for programmatic use
class Colors:
    BG          = "#0f1117"
    BG_RAISED   = "#161b22"
    BG_OVERLAY  = "#21262d"
    BG_HOVER    = "#30363d"
    BORDER      = "#21262d"
    BORDER_LITE = "#30363d"

    TEXT        = "#d1d5db"
    TEXT_DIM    = "#6b7280"
    TEXT_MUTED  = "#484f58"

    ACCENT      = "#f59e0b"
    ACCENT_BRIGHT = "#fbbf24"
    ACCENT_DARK = "#d97706"

    SUCCESS     = "#22c55e"
    WARNING     = "#eab308"
    ERROR       = "#ef4444"
    INFO        = "#3b82f6"

    def for_status(status: str) -> str:
        return {
            "running": Colors.SUCCESS,
            "starting": Colors.WARNING,
            "stopped": Colors.TEXT_MUTED,
            "error": Colors.ERROR,
        }.get(status, Colors.TEXT_DIM)


def load_theme() -> str:
    return DARK_QSS
