# SPDX-License-Identifier: GPL-3.0
"""Icon system — SVG icons loaded as QIcon.

Lucide-style line icons (24x24, 1.5px stroke).
Each icon visually represents its function.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import QSize, Qt, QRectF
from PySide6.QtSvg import QSvgRenderer

_ICONS_DIR = Path(__file__).parent.parent / "resources" / "icons"
_cache: dict[str, QIcon] = {}


def _tint_svg(svg_path: Path, color: str = "#d1d5db") -> bytes:
    """Read SVG and inject currentColor as the actual stroke/fill color."""
    data = svg_path.read_bytes()
    # Replace currentColor with actual color
    data = data.replace(b"currentColor", color.encode())
    return data


def icon(name: str, color: str = "#d1d5db", size: int = 20) -> QIcon:
    """Get a cached QIcon by name, tinted to color."""
    key = f"{name}:{color}:{size}"
    if key in _cache:
        return _cache[key]

    svg_path = _ICONS_DIR / f"{name}.svg"
    if not svg_path.exists():
        # Fallback: empty icon
        return QIcon()

    # Render SVG to pixmap with tint
    svg_data = _tint_svg(svg_path, color)
    renderer = QSvgRenderer(svg_data)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()

    qicon = QIcon(pixmap)
    _cache[key] = qicon
    return qicon


def pixmap(name: str, color: str = "#d1d5db", size: int = 20) -> QPixmap:
    """Get a QPixmap for direct drawing."""
    return icon(name, color, size).pixmap(QSize(size, size))


# Convenience: get icon with theme colors
from splatsdb_ui.utils.theme import Colors


def icon_normal(name: str) -> QIcon:
    return icon(name, Colors.TEXT)


def icon_dim(name: str) -> QIcon:
    return icon(name, Colors.TEXT_DIM)


def icon_accent(name: str) -> QIcon:
    return icon(name, Colors.ACCENT)


def icon_success(name: str) -> QIcon:
    return icon(name, Colors.SUCCESS)


def icon_error(name: str) -> QIcon:
    return icon(name, Colors.ERROR)


# Tab labels
def tab_label(view_id: str) -> str:
    """Plain text tab label — icon set via QTabWidget icon."""
    labels = {
        "welcome":     "Home",
        "search":      "Search",
        "collections": "Collections",
        "graph":       "Graph",
        "spatial":     "Spatial",
        "cluster":     "Cluster",
        "benchmark":   "Benchmark",
        "ocr":         "OCR",
        "config":      "Config",
    }
    return labels.get(view_id, view_id.title())


TAB_ICONS = {
    "welcome":     "home",
    "search":      "search",
    "collections": "database",
    "graph":       "graph",
    "spatial":     "spatial",
    "cluster":     "cluster",
    "benchmark":   "benchmark",
    "ocr":         "ocr",
    "config":      "config",
}
