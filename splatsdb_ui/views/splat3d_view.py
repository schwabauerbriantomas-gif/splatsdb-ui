# SPDX-License-Identifier: GPL-3.0
"""3D Gaussian Splat Visualization — authentic ellipsoid rendering.

Each vector node is rendered as a 3D Gaussian splat:
- Ellipsoid mesh (non-uniform scale + rotation)
- Per-vertex alpha with Gaussian falloff from center
- Translucent blending for overlapping splats
- Color-coded by cluster/category

This IS SplatsDB — the visual representation matches the data model.
"""

from __future__ import annotations

import colorsys
import os
import numpy as np
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QFrame,
)
from PySide6.QtCore import Signal, Qt, QTimer

import pyqtgraph as pg
import pyqtgraph.opengl as gl

from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon


# ---------------------------------------------------------------------------
# Gaussian Splat mesh generator
# ---------------------------------------------------------------------------

def _unit_sphere_mesh(rows: int = 10, cols: int = 10):
    """Generate unit sphere vertices and triangle faces."""
    verts = []
    for i in range(rows + 1):
        theta = np.pi * i / rows
        for j in range(cols + 1):
            phi = 2 * np.pi * j / cols
            x = np.sin(theta) * np.cos(phi)
            y = np.sin(theta) * np.sin(phi)
            z = np.cos(theta)
            verts.append([x, y, z])

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


# Cache the unit sphere — generated once, reused for every splat
_SPHERE_VERTS, _SPHERE_FACES = _unit_sphere_mesh(10, 10)


def build_splat_cloud_mesh(
    positions: np.ndarray,          # (N, 3)
    scales: np.ndarray,             # (N, 3) — ellipsoid semi-axes
    rotations: Optional[np.ndarray], # (N, 3, 3) or None
    colors: np.ndarray,             # (N, 3) or (N, 4) — RGB/RGBA
    opacities: np.ndarray,          # (N,) — peak opacity
):
    """Build a single merged mesh for all Gaussian splats.

    Returns (vertices, faces, vertex_colors) suitable for GLMeshItem.
    Per-vertex alpha uses Gaussian falloff from the ellipsoid center,
    giving the characteristic soft blobby look of 3D Gaussian Splatting.
    """
    n_splats = len(positions)
    n_verts = len(_SPHERE_VERTS)
    n_faces = len(_SPHERE_FACES)

    all_verts = np.empty((n_splats * n_verts, 3), dtype=np.float32)
    all_faces = np.empty((n_splats * n_faces, 3), dtype=np.uint32)
    all_colors = np.empty((n_splats * n_verts, 4), dtype=np.float32)

    base_colors = colors[:, :3].copy()
    if colors.shape[1] == 4:
        # Already RGBA — ignore, we compute our own alpha
        pass

    for i in range(n_splats):
        v = _SPHERE_VERTS.copy()

        # Scale to ellipsoid
        v *= scales[i]  # broadcast (n, 3) * (3,)

        # Rotate
        if rotations is not None:
            v = v @ rotations[i].T

        # Translate
        v += positions[i]

        # Gaussian alpha falloff: exp(-2 * ||normalized_dist||^2)
        centered = v - positions[i]
        norm_dist = np.sqrt(np.sum((centered / np.maximum(scales[i], 0.01)) ** 2, axis=1))
        # Softer falloff — peaks at center (0), drops at surface (1)
        alpha = opacities[i] * np.exp(-1.5 * norm_dist ** 2)
        # Ensure center vertices have near-full opacity
        alpha = np.clip(alpha, 0, 1)
        center_mask = norm_dist < 0.1
        alpha[center_mask] = opacities[i]

        # Store
        start_v = i * n_verts
        end_v = start_v + n_verts
        all_verts[start_v:end_v] = v
        all_colors[start_v:end_v, :3] = base_colors[i]
        all_colors[start_v:end_v, 3] = alpha

        start_f = i * n_faces
        end_f = start_f + n_faces
        all_faces[start_f:end_f] = _SPHERE_FACES + start_v

    return all_verts, all_faces, all_colors


def rotation_matrix_from_euler(rx: float, ry: float, rz: float) -> np.ndarray:
    """Create 3x3 rotation matrix from Euler angles (radians)."""
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)

    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float32)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float32)
    return Rz @ Ry @ Rx


# ---------------------------------------------------------------------------
# 3D Splat View
# ---------------------------------------------------------------------------

class Splat3DView(QWidget):
    """3D interactive visualization of Gaussian splats with connections."""

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
        self._scales: Optional[np.ndarray] = None
        self._rotations: Optional[np.ndarray] = None
        self._opacities: Optional[np.ndarray] = None
        self._splat_mesh: Optional[gl.GLMeshItem] = None
        self._lines: list[gl.GLLinePlotItem] = []
        self._highlight: Optional[gl.GLMeshItem] = None
        self._selected_idx: int = -1
        self._gl_available = False

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- Toolbar ----
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 8, 12, 8)
        toolbar.setSpacing(10)

        title = QLabel("Gaussian Splat Explorer")
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
        self.size_slider.setRange(3, 40)
        self.size_slider.setValue(12)
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
        toolbar_widget.setStyleSheet(
            f"background-color: {Colors.BG_RAISED}; border-bottom: 1px solid {Colors.BORDER};"
        )
        layout.addWidget(toolbar_widget)

        # ---- GL View (placeholder until GL init) ----
        self.gl_widget = QLabel(
            "Gaussian Splat Explorer\nConnect a display to enable 3D rendering"
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

        # ---- Info bar ----
        self.info_bar = QLabel(
            "Click a splat to inspect | Scroll to zoom | Drag to rotate"
        )
        self.info_bar.setStyleSheet(f"""
            color: {Colors.TEXT_DIM}; font-size: 11px; padding: 6px 12px;
            background-color: {Colors.BG_RAISED}; border-top: 1px solid {Colors.BORDER};
        """)
        layout.addWidget(self.info_bar)

        self.setStyleSheet(f"background-color: {Colors.BG};")

    # ------------------------------------------------------------------
    # GL initialization (deferred for headless compatibility)
    # ------------------------------------------------------------------

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
            grid.setColor(pg.mkColor(f"{Colors.BORDER}"))
            self.gl_widget.addItem(grid)

            # Axes
            axis_len = 25
            for clr, d in [
                (pg.mkColor("#ef4444"), np.array([[0, 0, 0], [axis_len, 0, 0]])),
                (pg.mkColor("#22c55e"), np.array([[0, 0, 0], [0, axis_len, 0]])),
                (pg.mkColor("#3b82f6"), np.array([[0, 0, 0], [0, 0, axis_len]])),
            ]:
                self.gl_widget.addItem(
                    gl.GLLinePlotItem(pos=d, color=clr, width=2, antialias=True)
                )

            self.layout().insertWidget(1, self.gl_widget, stretch=1)

            # Re-render data if loaded before GL was ready
            if self._positions is not None:
                self._render_splats()

        except Exception:
            self._gl_available = False

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_nodes(self, nodes: list[dict]):
        """Load splat nodes.

        Each node:
        {
            "id": str,
            "vector": list[float],
            "position": list[float],  # optional 3D override
            "scale": list[float],     # optional (sx, sy, sz) ellipsoid semi-axes
            "rotation": list[float],  # optional (rx, ry, rz) euler angles
            "color": list[float],     # optional RGB 0-1
            "opacity": float,         # optional
            "metadata": dict,
            "files": list[str],
            "connections": list[{"id": str, "score": float}],
        }
        """
        if not nodes:
            return

        self._nodes = {n["id"]: n for n in nodes}

        # --- Positions ---
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

        # --- Colors ---
        colors = []
        for i, node in enumerate(nodes):
            if "color" in node:
                c = node["color"][:3]
            else:
                hue = (i * 0.618033988749895) % 1.0
                c = colorsys.hsv_to_rgb(hue, 0.6, 0.85)
            colors.append(c)
        self._colors = np.array(colors, dtype=np.float32)

        # --- Splat scales (ellipsoid semi-axes) ---
        base = self.size_slider.value() / 10.0
        scales = []
        for node in nodes:
            if "scale" in node:
                scales.append(node["scale"][:3])
            else:
                # Vary size slightly per splat — looks organic
                s = base * (0.6 + 0.8 * np.random.random())
                scales.append([s, s * (0.5 + np.random.random()), s * (0.5 + np.random.random())])
        self._scales = np.array(scales, dtype=np.float32)

        # --- Rotations ---
        rotations = []
        for node in nodes:
            if "rotation" in node:
                rotations.append(rotation_matrix_from_euler(*node["rotation"][:3]))
            else:
                # Random rotation — each splat has unique orientation
                r = rotation_matrix_from_euler(
                    np.random.uniform(0, np.pi),
                    np.random.uniform(0, np.pi),
                    np.random.uniform(0, np.pi),
                )
                rotations.append(r)
        self._rotations = np.array(rotations, dtype=np.float32)

        # --- Opacities ---
        base_opacity = self.opacity_slider.value() / 100.0
        self._opacities = np.array(
            [node.get("opacity", base_opacity) for node in nodes], dtype=np.float32
        )

        # Render
        self._render_splats()

    def _render_splats(self):
        """Build and render the Gaussian splat cloud mesh."""
        if not self._gl_available or self._positions is None:
            self.info_bar.setText(
                f"{len(self._nodes)} splats loaded (3D unavailable)"
            )
            return

        self._clear_items()

        # Build merged ellipsoid mesh with Gaussian alpha
        verts, faces, vert_colors = build_splat_cloud_mesh(
            self._positions,
            self._scales,
            self._rotations,
            self._colors,
            self._opacities,
        )

        md = gl.MeshData(vertexes=verts, faces=faces, vertexColors=vert_colors)
        self._splat_mesh = gl.GLMeshItem(
            meshdata=md,
            smooth=True,
            shader='balloon',
            glOptions='translucent',
        )
        self.gl_widget.addItem(self._splat_mesh)

        # Connections
        self._draw_connections(list(self._nodes.values()))

        self.info_bar.setText(
            f"{len(self._nodes)} Gaussian splats | "
            f"{self._count_connections()} connections"
        )

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    def _draw_connections(self, nodes: list[dict]):
        if not self._gl_available:
            return
        for line in self._lines:
            try: self.gl_widget.removeItem(line)
            except Exception: pass
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
                # Color by strength
                if score > 0.8:
                    lc = (0.34, 0.83, 0.36, 0.35)
                elif score > 0.5:
                    lc = (0.96, 0.62, 0.04, 0.25)
                else:
                    lc = (0.94, 0.27, 0.27, 0.15)

                line = gl.GLLinePlotItem(
                    pos=np.array([self._positions[i], self._positions[j]]),
                    color=lc,
                    width=1.0 + score * 2.5,
                    antialias=True,
                )
                self.gl_widget.addItem(line)
                self._lines.append(line)
                edges += 1

    def _count_connections(self) -> int:
        total = sum(len(n.get("connections", [])) for n in self._nodes.values())
        return total // 2

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def select_node(self, node_id: str):
        if not self._gl_available or self._positions is None:
            return

        keys = list(self._nodes.keys())
        if node_id not in keys:
            return
        idx = keys.index(node_id)

        # Remove old highlight
        if self._highlight is not None:
            try: self.gl_widget.removeItem(self._highlight)
            except Exception: pass

        # Highlight: bright wireframe ellipsoid around selected splat
        sel_md = gl.MeshData.sphere(rows=16, cols=16)
        self._highlight = gl.GLMeshItem(
            meshdata=sel_md,
            smooth=True,
            color=pg.mkColor(Colors.ACCENT),
            shader='shaded',
            glOptions='translucent',
        )
        s = self._scales[idx] * 1.3  # Slightly larger than the splat
        self._highlight.scale(*s)
        self._highlight.translate(*self._positions[idx])
        self.gl_widget.addItem(self._highlight)

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

    # ------------------------------------------------------------------
    # Toolbar callbacks
    # ------------------------------------------------------------------

    def _on_layout_changed(self, name: str):
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
        elif name == "PCA" and mat.shape[1] >= 3:
            try:
                from sklearn.decomposition import PCA
                self._positions = PCA(n_components=3).fit_transform(mat).astype(np.float32)
            except ImportError:
                self._positions = mat[:, :3].copy()
        elif name in ("UMAP", "t-SNE"):
            try:
                if name == "UMAP":
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

        self._render_splats()

    def _on_size_changed(self, value: int):
        if self._scales is None:
            return
        base = value / 10.0
        for i in range(len(self._scales)):
            orig_ratio = self._scales[i] / (self._scales[i].max() + 0.01)
            self._scales[i] = orig_ratio * base
        self._render_splats()

    def _on_opacity_changed(self, value: int):
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
        if self._splat_mesh:
            try: self.gl_widget.removeItem(self._splat_mesh)
            except Exception: pass
            self._splat_mesh = None
        for line in self._lines:
            try: self.gl_widget.removeItem(line)
            except Exception: pass
        self._lines.clear()
        if self._highlight:
            try: self.gl_widget.removeItem(self._highlight)
            except Exception: pass
            self._highlight = None
