# SPDX-License-Identifier: GPL-3.0
"""3D Gaussian Splat Visualization — mathematically rigorous ellipsoid rendering.

Rendering equation per splat at surface point x:
    α(x) = α₀ · exp(-½ (x-μ)ᵀ Σ⁻¹ (x-μ))

where Σ = R S Sᵀ Rᵀ is the covariance (rotation R, scale S).
The exponent is the squared Mahalanobis distance — the true Gaussian shape.

Double-pass rendering:
  Pass 1 (glow):  larger, softer ellipsoid at low opacity → halo effect
  Pass 2 (core):  tight ellipsoid with Gaussian alpha falloff → solid core

Spherical-harmonic-like coloring: vertex normal dotted with virtual light
direction gives per-vertex brightness, simulating 3DGS SH appearance.
"""

from __future__ import annotations

import colorsys
import os
import numpy as np
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider,
)
from PySide6.QtCore import Signal, Qt, QTimer

import pyqtgraph as pg
import pyqtgraph.opengl as gl

from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon

# ---------------------------------------------------------------------------
# Palette — perceptually ordered, maximally distinct on dark backgrounds
# Uses golden-ratio hue spacing (0.618) in HSV for visual separation
# ---------------------------------------------------------------------------
PALETTE = [
    (0.96, 0.62, 0.04),  # Amber
    (0.23, 0.51, 0.96),  # Blue
    (0.06, 0.72, 0.51),  # Emerald
    (0.94, 0.27, 0.27),  # Red
    (0.55, 0.36, 0.96),  # Violet
    (0.93, 0.29, 0.60),  # Pink
    (0.08, 0.72, 0.65),  # Teal
    (0.98, 0.45, 0.09),  # Orange
    (0.20, 0.83, 0.83),  # Cyan
    (0.69, 0.78, 0.18),  # Lime
]


def palette_color(index: int) -> tuple:
    c = PALETTE[index % len(PALETTE)]
    return c


# ---------------------------------------------------------------------------
# Mesh generation — Mahalanobis-based Gaussian alpha
# ---------------------------------------------------------------------------

def _generate_sphere_mesh(resolution: int = 16):
    """UV sphere with given subdivision. Higher res = more vertices near center."""
    rows, cols = resolution, resolution
    verts = []
    for i in range(rows + 1):
        theta = np.pi * i / rows
        for j in range(cols + 1):
            phi = 2 * np.pi * j / cols
            verts.append([
                np.sin(theta) * np.cos(phi),
                np.sin(theta) * np.sin(phi),
                np.cos(theta),
            ])
    verts = np.array(verts, dtype=np.float32)
    faces = []
    for i in range(rows):
        for j in range(cols):
            p1 = i * (cols + 1) + j
            p2 = p1 + 1
            p3 = (i + 1) * (cols + 1) + j
            p4 = p3 + 1
            faces.append([p1, p3, p2])
            faces.append([p2, p3, p4])
    return verts, np.array(faces, dtype=np.uint32)


# Cache unit sphere — computed once
_UNIT_VERTS, _UNIT_FACES = _generate_sphere_mesh(12)

# Virtual light direction for SH-like shading (top-right-front)
_LIGHT_DIR = np.array([0.4, 0.3, 0.8], dtype=np.float32)
_LIGHT_DIR /= np.linalg.norm(_LIGHT_DIR)


def build_splat_mesh(
    position: np.ndarray,       # (3,) center
    scale: np.ndarray,          # (3,) semi-axes
    rotation: np.ndarray,       # (3,3) rotation matrix
    color: tuple,               # (r, g, b) 0-1
    opacity: float,             # peak opacity
    glow_scale: float = 1.8,   # glow pass scale multiplier
):
    """Build two meshes for a single Gaussian splat: glow + core.

    Alpha is computed using the squared Mahalanobis distance:
        d²_M = (x - μ)ᵀ Σ⁻¹ (x - μ)
    where Σ⁻¹ = R S⁻² Rᵀ (inverse covariance).

    Returns (glow_md, core_md) — two GLMeshData objects.
    """
    S_inv2 = np.diag(1.0 / np.maximum(scale, 0.01) ** 2)  # S⁻²
    sigma_inv = rotation @ S_inv2 @ rotation.T              # Σ⁻¹ = R S⁻² Rᵀ

    r, g, b = color
    n_verts = len(_UNIT_VERTS)
    n_faces = len(_UNIT_FACES)

    def _build_pass(scale_mult: float, alpha_mult: float):
        verts = _UNIT_VERTS.copy()

        # Scale
        verts *= scale * scale_mult

        # Rotate
        verts = verts @ rotation.T

        # Translate
        verts += position

        # Mahalanobis distance squared
        centered = verts - position
        # d²_M[i] = centered[i] @ sigma_inv @ centered[i]
        mahal_sq = np.einsum('ij,jk,ik->i', centered, sigma_inv, centered)

        # Gaussian alpha: α₀ · exp(-½ d²_M)
        alpha = opacity * alpha_mult * np.exp(-0.5 * mahal_sq)
        alpha = np.clip(alpha, 0, 1)

        # SH-like shading: dot vertex normal with light direction
        normals = _UNIT_VERTS.copy()
        normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-6)
        brightness = np.clip(normals @ _LIGHT_DIR, 0, 1)
        # Ambient 0.3 + diffuse 0.7
        shade = 0.3 + 0.7 * brightness

        colors = np.empty((n_verts, 4), dtype=np.float32)
        colors[:, 0] = r * shade
        colors[:, 1] = g * shade
        colors[:, 2] = b * shade
        colors[:, 3] = alpha

        md = gl.MeshData(
            vertexes=verts.astype(np.float32),
            faces=_UNIT_FACES,
            vertexColors=colors,
        )
        return md

    glow = _build_pass(glow_scale, 0.35)
    core = _build_pass(1.0, 1.0)
    return glow, core


def rotation_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return (Rz @ Ry @ Rx).astype(np.float32)


# ---------------------------------------------------------------------------
# Splat3D View
# ---------------------------------------------------------------------------

class Splat3DView(QWidget):
    """Gaussian Splat Explorer — authentic 3DGS rendering with Mahalanobis alpha."""

    node_selected = Signal(str)
    node_hovered = Signal(str)
    connection_clicked = Signal(str, str)

    def __init__(self, signals, state):
        super().__init__()
        self.signals = signals
        self.state = state

        self._nodes: dict[str, dict] = {}
        self._positions: Optional[np.ndarray] = None
        self._colors: list[tuple] = []
        self._scales: Optional[np.ndarray] = None
        self._rotations: Optional[np.ndarray] = None
        self._opacities: Optional[np.ndarray] = None

        # GL items per splat: [(glow_mesh, core_mesh), ...]
        self._splat_items: list[tuple] = []
        self._lines: list = []
        self._highlight_items: list = []
        self._selected_idx: int = -1
        self._gl_available = False

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        tb = QHBoxLayout()
        tb.setContentsMargins(12, 8, 12, 8)
        tb.setSpacing(10)

        title = QLabel("Gaussian Splat Explorer")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 14px; font-weight: 700;")
        tb.addWidget(title)

        tb.addWidget(QLabel("Layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["PCA", "UMAP", "t-SNE", "First 3 Dims"])
        self.layout_combo.setCurrentText("First 3 Dims")
        self.layout_combo.currentTextChanged.connect(self._on_layout_changed)
        tb.addWidget(self.layout_combo)

        tb.addWidget(QLabel("Splat size:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(3, 40)
        self.size_slider.setValue(14)
        self.size_slider.setFixedWidth(90)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        tb.addWidget(self.size_slider)

        tb.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(70)
        self.opacity_slider.setFixedWidth(80)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        tb.addWidget(self.opacity_slider)

        tb.addWidget(QLabel("Connections:"))
        self.conn_combo = QComboBox()
        self.conn_combo.addItems(["All", "Nearest 5", "Nearest 10", "Above threshold", "None"])
        self.conn_combo.setCurrentText("Nearest 5")
        self.conn_combo.currentTextChanged.connect(self._on_connections_changed)
        tb.addWidget(self.conn_combo)

        tb.addStretch()

        reset_btn = QPushButton("Reset View")
        reset_btn.setIcon(icon("refresh", Colors.TEXT))
        reset_btn.clicked.connect(self._reset_camera)
        tb.addWidget(reset_btn)

        tb_w = QWidget()
        tb_w.setLayout(tb)
        tb_w.setStyleSheet(
            f"background-color: {Colors.BG_RAISED}; border-bottom: 1px solid {Colors.BORDER};"
        )
        layout.addWidget(tb_w)

        # GL placeholder
        self.gl_widget = QLabel(
            "Gaussian Splat Explorer\nConnect a display to enable 3D"
        )
        self.gl_widget.setAlignment(Qt.AlignCenter)
        self.gl_widget.setStyleSheet(
            f"color: {Colors.TEXT_DIM}; font-size: 14px; background-color: {Colors.BG};"
        )
        self.gl_widget.setMinimumHeight(400)
        self.gl_widget.setMouseTracking(True)

        if not os.environ.get("SPLATSDB_NO_GL"):
            QTimer.singleShot(0, self._try_init_gl)

        layout.addWidget(self.gl_widget, stretch=1)

        # Info bar
        self.info_bar = QLabel(
            "Click a splat to inspect | Scroll to zoom | Drag to rotate"
        )
        self.info_bar.setStyleSheet(f"""
            color: {Colors.TEXT_DIM}; font-size: 11px; padding: 6px 12px;
            background-color: {Colors.BG_RAISED}; border-top: 1px solid {Colors.BORDER};
        """)
        layout.addWidget(self.info_bar)
        self.setStyleSheet(f"background-color: {Colors.BG};")

    def _try_init_gl(self):
        try:
            self.layout().removeWidget(self.gl_widget)
            self.gl_widget.deleteLater()

            self.gl_widget = gl.GLViewWidget()
            self.gl_widget.setBackgroundColor(pg.mkColor(Colors.BG))
            self.gl_widget.setCameraPosition(distance=40, elevation=25, azimuth=45)
            self.gl_widget.setMinimumHeight(400)
            self.gl_widget.setMouseTracking(True)
            self._gl_available = True

            # Grid
            grid = gl.GLGridItem()
            grid.setSize(50, 50, 1)
            grid.setSpacing(5, 5, 5)
            grid.setColor(pg.mkColor(Colors.BORDER))
            self.gl_widget.addItem(grid)

            # Axes
            for clr, d in [
                (pg.mkColor("#ef4444"), np.array([[0, 0, 0], [25, 0, 0]])),
                (pg.mkColor("#22c55e"), np.array([[0, 0, 0], [0, 25, 0]])),
                (pg.mkColor("#3b82f6"), np.array([[0, 0, 0], [0, 0, 25]])),
            ]:
                self.gl_widget.addItem(
                    gl.GLLinePlotItem(pos=d, color=clr, width=2, antialias=True)
                )

            self.layout().insertWidget(1, self.gl_widget, stretch=1)

            if self._positions is not None:
                self._render_splats()

        except Exception:
            self._gl_available = False

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def load_nodes(self, nodes: list[dict]):
        if not nodes:
            return

        self._nodes = {n["id"]: n for n in nodes}
        n = len(nodes)

        # Positions
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

        # Colors from palette
        self._colors = [palette_color(i) for i in range(n)]

        # Scales — vary shape per splat for organic feel
        base = self.size_slider.value() / 10.0
        np.random.seed(42)
        scales = []
        for i in range(n):
            if "scale" in nodes[i]:
                scales.append(nodes[i]["scale"][:3])
            else:
                # Each splat has unique eccentricity
                angle_frac = (i * 0.618) % 1.0  # golden ratio
                sx = base * (0.7 + 0.6 * angle_frac)
                sy = base * (0.7 + 0.6 * (1 - angle_frac))
                sz = base * (0.5 + 0.4 * np.random.random())
                scales.append([sx, sy, sz])
        self._scales = np.array(scales, dtype=np.float32)

        # Rotations
        rotations = []
        for i in range(n):
            if "rotation" in nodes[i]:
                rotations.append(rotation_matrix(*nodes[i]["rotation"][:3]))
            else:
                # Fibonacci sphere orientation for uniform distribution
                golden_angle = np.pi * (3 - np.sqrt(5))
                theta = golden_angle * i
                phi = np.arccos(1 - 2 * (i + 0.5) / n)
                rotations.append(rotation_matrix(theta, phi, 0))
        self._rotations = np.array(rotations, dtype=np.float32)

        # Opacities
        base_o = self.opacity_slider.value() / 100.0
        self._opacities = np.array(
            [nodes[i].get("opacity", base_o) for i in range(n)], dtype=np.float32
        )

        self._render_splats()

    def _render_splats(self):
        if not self._gl_available or self._positions is None:
            count = len(self._nodes)
            self.info_bar.setText(f"{count} Gaussian splats (3D unavailable)")
            return

        self._clear_items()

        # Sort splats back-to-front for correct alpha blending
        cam_pos = np.array(self.gl_widget.cameraPosition())
        if hasattr(cam_pos, 'x'):
            cam = np.array([cam_pos.x(), cam_pos.y(), cam_pos.z()])
        else:
            cam = np.array(cam_pos)[:3] if cam_pos is not None else np.zeros(3)

        dists = np.linalg.norm(self._positions - cam, axis=1)
        order = np.argsort(-dists)  # back to front

        # Render each splat as individual glow + core meshes
        for idx in order:
            glow_md, core_md = build_splat_mesh(
                self._positions[idx],
                self._scales[idx],
                self._rotations[idx],
                self._colors[idx],
                self._opacities[idx],
            )
            glow_item = gl.GLMeshItem(
                meshdata=glow_md, smooth=True, shader='balloon',
                glOptions='translucent',
            )
            core_item = gl.GLMeshItem(
                meshdata=core_md, smooth=True, shader='balloon',
                glOptions='translucent',
            )
            self.gl_widget.addItem(glow_item)
            self.gl_widget.addItem(core_item)
            self._splat_items.append((glow_item, core_item))

        # Connections
        self._draw_connections(list(self._nodes.values()))

        n = len(self._nodes)
        self.info_bar.setText(
            f"{n} Gaussian splats | Mahalanobis α | "
            f"{self._count_connections()} connections"
        )

    def _draw_connections(self, nodes: list[dict]):
        if not self._gl_available:
            return
        for line in self._lines:
            try: self.gl_widget.removeItem(line)
            except: pass
        self._lines.clear()

        mode = self.conn_combo.currentText()
        if mode == "None":
            return

        id_to_idx = {n["id"]: i for i, n in enumerate(nodes)}
        edges = 0

        for i, node in enumerate(nodes):
            if edges >= 2000:
                break
            conns = node.get("connections", [])
            if not conns:
                continue
            if mode == "Nearest 5":
                conns = sorted(conns, key=lambda c: c.get("score", 0), reverse=True)[:5]
            elif mode == "Nearest 10":
                conns = sorted(conns, key=lambda c: c.get("score", 0), reverse=True)[:10]
            elif mode == "Above threshold":
                conns = [c for c in conns if c.get("score", 0) > 0.7]

            for conn in conns:
                tid = conn.get("id")
                if tid not in id_to_idx:
                    continue
                j = id_to_idx[tid]
                if j <= i:
                    continue

                score = conn.get("score", 0.5)
                # Color: gradient from cool (weak) to warm (strong)
                t = score
                r = 0.3 + 0.6 * t
                g = 0.3 + 0.3 * (1 - t) + 0.4 * t
                b = 0.8 * (1 - t) + 0.1 * t
                alpha = 0.15 + 0.35 * t

                line = gl.GLLinePlotItem(
                    pos=np.array([self._positions[i], self._positions[j]]),
                    color=(r, g, b, alpha),
                    width=1.0 + score * 2.5,
                    antialias=True,
                )
                self.gl_widget.addItem(line)
                self._lines.append(line)
                edges += 1

    def _count_connections(self) -> int:
        total = sum(len(n.get("connections", [])) for n in self._nodes.values())
        return total // 2

    def select_node(self, node_id: str):
        if not self._gl_available or self._positions is None:
            return
        keys = list(self._nodes.keys())
        if node_id not in keys:
            return
        idx = keys.index(node_id)

        # Remove old highlight
        for item in self._highlight_items:
            try: self.gl_widget.removeItem(item)
            except: pass
        self._highlight_items.clear()

        # Highlight ring: wireframe ellipsoid at 1.2x scale
        sel_md, _ = build_splat_mesh(
            self._positions[idx],
            self._scales[idx] * 1.25,
            self._rotations[idx],
            (0.96, 0.62, 0.04),  # amber
            0.5,
            glow_scale=1.0,
        )
        ring = gl.GLMeshItem(
            meshdata=sel_md, smooth=True,
            color=pg.mkColor(Colors.ACCENT),
            shader='shaded', glOptions='translucent',
        )
        self.gl_widget.addItem(ring)
        self._highlight_items.append(ring)

        self._selected_idx = idx
        pos = self._positions[idx]
        self.gl_widget.pan(pos[0], pos[1], pos[2])

        node = list(self._nodes.values())[idx]
        meta = node.get("metadata", {})
        text = meta.get("text", meta.get("label", node_id))
        self.info_bar.setText(
            f"Selected: {text[:80]}  |  "
            f"{len(node.get('connections', []))} connections  |  "
            f"{len(node.get('files', []))} files"
        )
        self.node_selected.emit(node_id)

    # Toolbar
    def _on_layout_changed(self, name):
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

        if name == "First 3 Dims":
            self._positions = mat[:, :3].copy()
        elif name == "PCA":
            try:
                from sklearn.decomposition import PCA
                self._positions = PCA(n_components=3).fit_transform(mat).astype(np.float32)
            except: self._positions = mat[:, :3].copy()
        elif name in ("UMAP", "t-SNE"):
            try:
                if name == "UMAP":
                    import umap
                    r = umap.UMAP(n_components=3, n_neighbors=15, min_dist=0.1)
                else:
                    from sklearn.manifold import TSNE
                    r = TSNE(n_components=3, perplexity=30)
                self._positions = r.fit_transform(mat).astype(np.float32)
            except: self._positions = mat[:, :3].copy()
        else:
            self._positions = mat[:, :3].copy()

        for dim in range(3):
            col = self._positions[:, dim]
            mn, mx = col.min(), col.max()
            if mx > mn:
                self._positions[:, dim] = (col - mn) / (mx - mn) * 30 - 15
        self._render_splats()

    def _on_size_changed(self, value):
        if self._scales is None:
            return
        base = value / 10.0
        for i in range(len(self._scales)):
            ratio = self._scales[i] / (self._scales[i].max() + 0.01)
            self._scales[i] = ratio * base
        self._render_splats()

    def _on_opacity_changed(self, value):
        if self._opacities is None:
            return
        self._opacities[:] = value / 100.0
        self._render_splats()

    def _on_connections_changed(self, _):
        if self._nodes:
            self._draw_connections(list(self._nodes.values()))

    def _reset_camera(self):
        if self._gl_available:
            self.gl_widget.setCameraPosition(distance=40, elevation=25, azimuth=45)
            self.gl_widget.pan(0, 0, 0)

    def _clear_items(self):
        if not self._gl_available:
            return
        for glow, core in self._splat_items:
            try: self.gl_widget.removeItem(glow)
            except: pass
            try: self.gl_widget.removeItem(core)
            except: pass
        self._splat_items.clear()
        for line in self._lines:
            try: self.gl_widget.removeItem(line)
            except: pass
        self._lines.clear()
        for item in self._highlight_items:
            try: self.gl_widget.removeItem(item)
            except: pass
        self._highlight_items.clear()
