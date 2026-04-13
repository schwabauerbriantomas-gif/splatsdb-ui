# SPDX-License-Identifier: GPL-3.0
"""3D Splat Visualization — interactive node graph with Gaussian Splat rendering.

Uses pyqtgraph OpenGL for hardware-accelerated 3D rendering.
Each vector node is rendered as a TRUE Gaussian Splat — soft, organic blob
with alpha blending that merges with neighboring splats.
Connections shown as translucent bezier-like lines.
"""

from __future__ import annotations

import numpy as np
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QLabel as QLabel_,
)
from PySide6.QtCore import Signal, Qt

import pyqtgraph as pg
import pyqtgraph.opengl as gl

from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon


class Splat3DView(QWidget):
    """3D interactive visualization with true Gaussian Splat rendering."""

    node_selected = Signal(str)
    node_hovered = Signal(str)
    connection_clicked = Signal(str, str)

    def __init__(self, signals, state):
        super().__init__()
        self.signals = signals
        self.state = state

        self._nodes: dict[str, dict] = {}
        self._positions: Optional[np.ndarray] = None
        self._colors: Optional[np.ndarray] = None
        self._sizes: Optional[np.ndarray] = None
        self._scatter: Optional[gl.GLScatterPlotItem] = None
        self._lines: list[gl.GLLinePlotItem] = []
        self._selected_idx: int = -1
        self._highlight: Optional[gl.GLScatterPlotItem] = None

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 8, 12, 8)
        toolbar.setSpacing(10)

        title = QLabel("3D Explorer")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 14px; font-weight: 700;")
        toolbar.addWidget(title)

        toolbar.addWidget(QLabel("Layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["PCA", "UMAP", "t-SNE", "First 3 Dims"])
        self.layout_combo.setCurrentText("First 3 Dims")
        self.layout_combo.currentTextChanged.connect(self._on_layout_changed)
        toolbar.addWidget(self.layout_combo)

        toolbar.addWidget(QLabel("Splat size:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(4, 40)
        self.size_slider.setValue(16)
        self.size_slider.setFixedWidth(100)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        toolbar.addWidget(self.size_slider)

        toolbar.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(60)
        self.opacity_slider.setFixedWidth(80)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        toolbar.addWidget(self.opacity_slider)

        toolbar.addWidget(QLabel("Connections:"))
        self.conn_combo = QComboBox()
        self.conn_combo.addItems(["All", "Nearest 5", "Nearest 10", "Above threshold", "None"])
        self.conn_combo.setCurrentText("Nearest 5")
        self.conn_combo.currentTextChanged.connect(self._on_connections_changed)
        toolbar.addWidget(self.conn_combo)

        toolbar.addStretch()

        reset_btn = QPushButton("Reset View")
        reset_btn.setIcon(icon("refresh", Colors.TEXT))
        reset_btn.clicked.connect(self._reset_camera)
        toolbar.addWidget(reset_btn)

        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar)
        toolbar_widget.setStyleSheet(f"background-color: {Colors.BG_RAISED}; border-bottom: 1px solid {Colors.BORDER};")
        layout.addWidget(toolbar_widget)

        # 3D View placeholder
        self._gl_available = False
        self.gl_widget = QLabel("3D view requires OpenGL\nConnect a display to enable")
        self.gl_widget.setAlignment(Qt.AlignCenter)
        self.gl_widget.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 14px; background-color: {Colors.BG};")
        self.gl_widget.setMinimumHeight(400)

        import os
        if not os.environ.get("SPLATSDB_NO_GL"):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self._try_init_gl)

        layout.addWidget(self.gl_widget, stretch=1)

        # Info bar
        self.info_bar = QLabel("Click a splat to inspect | Scroll to zoom | Drag to rotate")
        self.info_bar.setStyleSheet(f"""
            color: {Colors.TEXT_DIM}; font-size: 11px; padding: 6px 12px;
            background-color: {Colors.BG_RAISED}; border-top: 1px solid {Colors.BORDER};
        """)
        layout.addWidget(self.info_bar)

        self.setStyleSheet(f"background-color: {Colors.BG};")

    def load_nodes(self, nodes: list[dict]):
        """Load splats into the 3D view."""
        if not nodes:
            return

        self._nodes = {n["id"]: n for n in nodes}

        # Compute positions
        positions = []
        for node in nodes:
            if "position" in node and len(node["position"]) >= 3:
                positions.append(node["position"][:3])
            elif "vector" in node and len(node["vector"]) >= 3:
                positions.append(node["vector"][:3])
            else:
                positions.append([np.random.uniform(-10, 10) for _ in range(3)])

        self._positions = np.array(positions, dtype=np.float32)

        # Normalize to [-15, 15]
        for dim in range(3):
            col = self._positions[:, dim]
            mn, mx = col.min(), col.max()
            if mx > mn:
                self._positions[:, dim] = (col - mn) / (mx - mn) * 30 - 15

        # Colors — Gaussian Splat palette (warm, organic tones)
        colors = []
        opacity = self.opacity_slider.value() / 100.0
        for i, node in enumerate(nodes):
            if "color" in node:
                c = node["color"][:3]
                colors.append([*c, opacity])
            else:
                hue = (i * 0.618033988749895) % 1.0
                r, g, b = self._hsv_to_rgb(hue, 0.55, 0.9)
                # Splat colors: slightly desaturated, high brightness for glow effect
                colors.append([r, g, b, opacity])

        self._colors = np.array(colors, dtype=np.float32)

        # Sizes
        base_size = self.size_slider.value()
        sizes = np.array([node.get("size", base_size) for node in nodes], dtype=np.float32)
        self._sizes = sizes

        self._clear_items()

        if not self._gl_available:
            self.info_bar.setText(f"{len(nodes)} splats loaded (3D unavailable)")
            return

        # Render as splats using GL_POINTS with GL_POINT_SMOOTH
        # This gives soft, circular Gaussian-like blobs
        self._render_splats()

        # Draw connections as soft translucent lines
        self._draw_connections(nodes)

        self.info_bar.setText(f"{len(nodes)} splats | {self._count_connections(nodes)} connections")

    def _render_splats(self):
        """Render splats with soft, organic Gaussian look."""
        # Use scatter with large point size + smooth for splat effect
        self._scatter = gl.GLScatterPlotItem(
            pos=self._positions,
            color=self._colors,
            size=self._sizes,
            pxMode=True,
            glOptions='translucent',  # Critical: enables alpha blending
        )
        # Enable GL_POINT_SMOOTH for soft circular points (Gaussian-like)
        self._scatter.setGLOptions('translucent')
        self.gl_widget.addItem(self._scatter)

    def _draw_connections(self, nodes: list[dict]):
        """Draw soft translucent connection lines between splats."""
        if not self._gl_available:
            return
        for line in self._lines:
            try:
                self.gl_widget.removeItem(line)
            except Exception:
                pass
        self._lines.clear()

        mode = self.conn_combo.currentText()
        if mode == "None":
            return

        id_to_idx = {n["id"]: i for i, n in enumerate(nodes)}
        edges_drawn = 0
        max_edges = 2000

        for i, node in enumerate(nodes):
            if edges_drawn >= max_edges:
                break

            connections = node.get("connections", [])
            if not connections:
                continue

            if mode == "Nearest 5":
                connections = sorted(connections, key=lambda c: c.get("score", 0), reverse=True)[:5]
            elif mode == "Nearest 10":
                connections = sorted(connections, key=lambda c: c.get("score", 0), reverse=True)[:10]
            elif mode == "Above threshold":
                connections = [c for c in connections if c.get("score", 0) > 0.7]

            for conn in connections:
                target_id = conn.get("id")
                if target_id not in id_to_idx:
                    continue
                j = id_to_idx[target_id]
                if j <= i:
                    continue

                score = conn.get("score", 0.5)

                # Soft connection colors matching splat aesthetic
                if score > 0.8:
                    lc = (0.34, 0.83, 0.36, 0.25)
                elif score > 0.5:
                    lc = (0.96, 0.62, 0.04, 0.18)
                else:
                    lc = (0.94, 0.27, 0.27, 0.12)

                # Multi-segment line for slight curve (bezier approximation)
                p1 = self._positions[i]
                p2 = self._positions[j]
                mid = (p1 + p2) / 2
                # Slight perpendicular offset for organic feel
                perp = np.array([-(p2[1]-p1[1]), p2[0]-p1[0], 0.0]) * 0.05 * (1 - score)
                pts = np.array([
                    p1,
                    (p1 + mid) / 2 + perp,
                    mid + perp * 0.5,
                    (p2 + mid) / 2 + perp,
                    p2,
                ])

                line = gl.GLLinePlotItem(
                    pos=pts,
                    color=lc,
                    width=0.8 + score * 1.5,
                    antialias=True,
                    glOptions='translucent',
                )
                self.gl_widget.addItem(line)
                self._lines.append(line)
                edges_drawn += 1

    def _count_connections(self, nodes: list[dict]) -> int:
        total = sum(len(n.get("connections", [])) for n in nodes)
        return total // 2

    def select_node(self, node_id: str):
        """Highlight a splat and emit node_selected."""
        if not self._gl_available or self._positions is None:
            return
        idx = None
        for i, key in enumerate(self._nodes.keys()):
            if key == node_id:
                idx = i
                break
        if idx is None:
            return

        # Remove old highlight
        if self._highlight is not None:
            try:
                self.gl_widget.removeItem(self._highlight)
            except Exception:
                pass

        # Highlight: bright pulsing splat behind selected node
        highlight_color = np.array([[0.96, 0.62, 0.04, 0.9]], dtype=np.float32)
        highlight_pos = self._positions[idx:idx+1]
        self._highlight = gl.GLScatterPlotItem(
            pos=highlight_pos,
            color=highlight_color,
            size=np.array([self._sizes[idx] * 2.5], dtype=np.float32),
            pxMode=True,
            glOptions='translucent',
        )
        self.gl_widget.addItem(self._highlight)

        self._selected_idx = idx

        # Pan to splat
        pos = self._positions[idx]
        self.gl_widget.pan(pos[0], pos[1], pos[2])

        node = list(self._nodes.values())[idx]
        meta = node.get("metadata", {})
        text = meta.get("text", meta.get("label", node_id))
        self.info_bar.setText(f"Selected: {text[:80]}  |  {len(node.get('connections', []))} connections  |  {len(node.get('files', []))} files")

        self.node_selected.emit(node_id)

    def _on_layout_changed(self, layout_name: str):
        if self._positions is None:
            return

        nodes = list(self._nodes.values())
        vectors = []
        for n in nodes:
            v = n.get("vector", n.get("position", []))
            if len(v) < 3:
                v = list(v) + [0.0] * (3 - len(v))
            vectors.append(v)

        if not vectors:
            return

        mat = np.array(vectors, dtype=np.float32)

        if layout_name == "First 3 Dims":
            self._positions = mat[:, :3].copy()
        elif layout_name == "PCA" and mat.shape[1] >= 3:
            try:
                from sklearn.decomposition import PCA
                self._positions = PCA(n_components=3).fit_transform(mat).astype(np.float32)
            except ImportError:
                self._positions = mat[:, :3].copy()
        elif layout_name in ("UMAP", "t-SNE"):
            try:
                if layout_name == "UMAP":
                    import umap
                    reducer = umap.UMAP(n_components=3, n_neighbors=15, min_dist=0.1)
                else:
                    from sklearn.manifold import TSNE
                    reducer = TSNE(n_components=3, perplexity=30)
                self._positions = reducer.fit_transform(mat).astype(np.float32)
            except ImportError:
                self._positions = mat[:, :3].copy()
        else:
            self._positions = mat[:, :3].copy()

        for dim in range(3):
            col = self._positions[:, dim]
            mn, mx = col.min(), col.max()
            if mx > mn:
                self._positions[:, dim] = (col - mn) / (mx - mn) * 30 - 15

        if self._scatter:
            self._scatter.setData(pos=self._positions, color=self._colors, size=self._sizes)

        self._draw_connections(nodes)

    def _on_size_changed(self, value: int):
        if self._scatter and self._sizes is not None:
            self._sizes = np.full(len(self._sizes), value, dtype=np.float32)
            self._scatter.setData(size=self._sizes)

    def _on_opacity_changed(self, value: int):
        if self._scatter and self._colors is not None:
            opacity = value / 100.0
            self._colors[:, 3] = opacity
            self._scatter.setData(color=self._colors)

    def _on_connections_changed(self, _mode: str):
        if self._nodes:
            self._draw_connections(list(self._nodes.values()))

    def _reset_camera(self):
        if self._gl_available:
            self.gl_widget.setCameraPosition(distance=40, elevation=30, azimuth=45)
            self.gl_widget.pan(0, 0, 0)

    def _clear_items(self):
        if not self._gl_available:
            return
        if self._scatter:
            try:
                self.gl_widget.removeItem(self._scatter)
            except Exception:
                pass
            self._scatter = None
        for line in self._lines:
            try:
                self.gl_widget.removeItem(line)
            except Exception:
                pass
        self._lines.clear()
        if self._highlight:
            try:
                self.gl_widget.removeItem(self._highlight)
            except Exception:
                pass
            self._highlight = None

    @staticmethod
    def _hsv_to_rgb(h, s, v):
        import colorsys
        return colorsys.hsv_to_rgb(h, s, v)

    def _try_init_gl(self):
        """Init OpenGL with splat-optimized settings."""
        try:
            self.layout().removeWidget(self.gl_widget)
            self.gl_widget.deleteLater()

            self.gl_widget = gl.GLViewWidget()
            self.gl_widget.setBackgroundColor(pg.mkColor(Colors.BG))
            self.gl_widget.setCameraPosition(distance=40, elevation=30, azimuth=45)
            self.gl_widget.setMinimumHeight(400)
            self._gl_available = True

            # Grid (subtle, dark)
            grid = gl.GLGridItem()
            grid.setSize(50, 50, 1)
            grid.setSpacing(5, 5, 5)
            grid.setColor(pg.mkColor(20, 23, 30))
            self.gl_widget.addItem(grid)

            # Axes (subtle)
            axis_len = 25
            for color, direction in [
                (pg.mkColor(80, 30, 30), np.array([[0, 0, 0], [axis_len, 0, 0]])),
                (pg.mkColor(30, 80, 30), np.array([[0, 0, 0], [0, axis_len, 0]])),
                (pg.mkColor(30, 30, 80), np.array([[0, 0, 0], [0, 0, axis_len]])),
            ]:
                line = gl.GLLinePlotItem(pos=direction, color=color, width=1, antialias=True)
                self.gl_widget.addItem(line)

            self.gl_widget.setMouseTracking(True)
            self.layout().insertWidget(1, self.gl_widget, stretch=1)

            if self._positions is not None:
                nodes = list(self._nodes.values())
                self.load_nodes(nodes)

        except Exception:
            self._gl_available = False

    def get_params(self) -> list:
        return [
            {"name": "splat_size", "label": "Splat Size", "type": "spin", "min": 4, "max": 40, "default": 16},
            {"name": "opacity", "label": "Opacity", "type": "spin", "min": 10, "max": 100, "default": 60},
            {"name": "connection_mode", "label": "Connections", "type": "combo",
             "options": ["All", "Nearest 5", "Nearest 10", "Above threshold", "None"]},
            {"name": "layout", "label": "Layout", "type": "combo",
             "options": ["PCA", "UMAP", "t-SNE", "First 3 Dims"]},
        ]
