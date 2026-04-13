# SPDX-License-Identifier: GPL-3.0
"""3D Gaussian Splat Visualization — dual-mode renderer.

Rendering equation per splat at surface point x:
    α(x) = α₀ · exp(-½ (x-μ)ᵀ Σ⁻¹ (x-μ))

Dual rendering:
  GL mode:   Full 3D ellipsoid meshes with Mahalanobis per-vertex alpha
  2D mode:   QPainter with QRadialGradient ellipses — same Gaussian math,
             projected onto screen plane with proper covariance transform

2D projection math:
  Σ₂D = P Σ₃D Pᵀ  where P is orthographic projection onto view plane
  Eigendecompose Σ₂D = Q Λ Qᵀ → ellipse semi-axes = √λᵢ, angle = atan2(q₂₁, q₁₁)
  QRadialGradient stops emulate exp(-½ d²_M) in 2D

Both modes share the same data pipeline and toolbar controls.
"""

from __future__ import annotations

import colorsys
import math
import os
import numpy as np
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QTimer, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QRadialGradient, QPainterPath, QTransform,
)

from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
PALETTE = [
    (0.96, 0.62, 0.04),
    (0.23, 0.51, 0.96),
    (0.06, 0.72, 0.51),
    (0.94, 0.27, 0.27),
    (0.55, 0.36, 0.96),
    (0.93, 0.29, 0.60),
    (0.08, 0.72, 0.65),
    (0.98, 0.45, 0.09),
    (0.20, 0.83, 0.83),
    (0.69, 0.78, 0.18),
]

def palette_color(index: int) -> tuple:
    return PALETTE[index % len(PALETTE)]

def rotation_matrix(rx, ry, rz):
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return (Rz @ Ry @ Rx).astype(np.float32)

# ---------------------------------------------------------------------------
# GL mesh builder (kept for when GL is available)
# ---------------------------------------------------------------------------
try:
    import pyqtgraph as pg
    import pyqtgraph.opengl as gl
    _GL_OK = True
except ImportError:
    _GL_OK = False

_UNIT_VERTS = _UNIT_FACES = None

def _ensure_sphere():
    global _UNIT_VERTS, _UNIT_FACES
    if _UNIT_VERTS is not None:
        return
    rows = cols = 16
    verts = []
    for i in range(rows + 1):
        theta = np.pi * i / rows
        for j in range(cols + 1):
            phi = 2 * np.pi * j / cols
            verts.append([np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta)])
    _UNIT_VERTS = np.array(verts, dtype=np.float32)
    faces = []
    for i in range(rows):
        for j in range(cols):
            p1 = i*(cols+1)+j; p2 = p1+1; p3 = (i+1)*(cols+1)+j; p4 = p3+1
            faces.append([p1, p3, p2]); faces.append([p2, p3, p4])
    _UNIT_FACES = np.array(faces, dtype=np.uint32)

_LIGHT_DIR = np.array([0.4, 0.3, 0.8], dtype=np.float32)
_LIGHT_DIR /= np.linalg.norm(_LIGHT_DIR)

def build_splat_mesh(position, scale, rotation, color, opacity, glow_scale=1.8):
    _ensure_sphere()
    S_inv2 = np.diag(1.0 / np.maximum(scale, 0.01) ** 2)
    sigma_inv = rotation @ S_inv2 @ rotation.T
    r, g, b = color

    def _pass(sm, am):
        v = _UNIT_VERTS.copy() * scale * sm @ rotation.T + position
        c = v - position
        mahal = np.einsum('ij,jk,ik->i', c, sigma_inv, c)
        alpha = np.clip(opacity * am * np.exp(-0.5 * mahal), 0, 1)
        n = _UNIT_VERTS.copy()
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
        shade = 0.3 + 0.7 * np.clip(n @ _LIGHT_DIR, 0, 1)
        cols = np.empty((len(v), 4), dtype=np.float32)
        cols[:, 0] = r * shade; cols[:, 1] = g * shade; cols[:, 2] = b * shade; cols[:, 3] = alpha
        return gl.MeshData(vertexes=v.astype(np.float32), faces=_UNIT_FACES, vertexColors=cols)

    return _pass(glow_scale, 0.35), _pass(1.0, 1.0)


# ---------------------------------------------------------------------------
# 2D Splat Canvas — QPainter fallback with same Gaussian math
# ---------------------------------------------------------------------------

class Splat2DCanvas(QWidget):
    """Renders Gaussian splats in 2D using QPainter.

    Each splat is an ellipse whose shape comes from projecting the 3D covariance
    onto the XY plane:
        Σ₂D = Pₓᵧ Σ₃D Pₓᵧᵀ
    Eigendecompose Σ₂D → semi-axes and rotation angle for the ellipse.
    QRadialGradient with Gaussian stops emulates the Mahalanobis alpha falloff.
    """

    node_clicked = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

        self._nodes: dict = {}
        self._positions: Optional[np.ndarray] = None
        self._colors: list = []
        self._scales: Optional[np.ndarray] = None
        self._rotations: Optional[np.ndarray] = None
        self._opacities: Optional[np.ndarray] = None
        self._connections_2d: list = []
        self._selected_idx: int = -1
        self._hovered_idx: int = -1

        self._view_rx = 0.35   # elevation angle (radians)
        self._view_ry = 0.5    # azimuth angle
        self._drag_start = None
        self._pan_start = None
        self._pan_offset = np.zeros(2)
        self._zoom = 1.0

    def set_data(self, nodes, positions, colors, scales, rotations, opacities):
        self._nodes = nodes
        self._positions = positions
        self._colors = colors
        self._scales = scales
        self._rotations = rotations
        self._opacities = opacities
        self._compute_connections()
        self.update()

    def _project(self, pos3d):
        """Orthographic projection with rotation: XY plane rotated by view angles."""
        rx, ry = self._view_rx, self._view_ry
        # Rotate around Y (azimuth), then X (elevation)
        cy, sy = np.cos(ry), np.sin(ry)
        cx, sx = np.cos(rx), np.sin(rx)
        x, y, z = pos3d
        # Y rotation
        x1 = x * cy + z * sy
        z1 = -x * sy + z * cy
        # X rotation
        y1 = y * cx - z1 * sx
        z2 = y * sx + z1 * cx
        return x1, y1, z2

    def _to_screen(self, px, py):
        w, h = self.width(), self.height()
        margin = 80
        sx = (w / 2 + (px + self._pan_offset[0]) * self._zoom * (w - 2*margin) / 35)
        sy = (h / 2 - (py + self._pan_offset[1]) * self._zoom * (h - 2*margin) / 35)
        return sx, sy

    def paintEvent(self, event):
        if self._positions is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(Colors.BG))

        # Subtle grid
        painter.setPen(QPen(QColor(255, 255, 255, 8), 0.5))
        for x in range(0, w, 30):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, 30):
            painter.drawLine(0, y, w, y)

        n = len(self._positions)

        # Project all positions
        projected = []
        depths = []
        for i in range(n):
            px, py, pz = self._project(self._positions[i])
            sx, sy = self._to_screen(px, py)
            projected.append((sx, sy))
            depths.append(pz)

        # Sort back-to-front by depth
        order = np.argsort(depths)

        # Draw connections first (behind splats)
        self._paint_connections(painter, projected)

        # Draw each splat
        for idx in order:
            self._paint_splat(painter, idx, projected[idx])

        # Selected highlight
        if 0 <= self._selected_idx < n:
            self._paint_selection_ring(painter, self._selected_idx, projected[self._selected_idx])

        # Legend
        self._paint_legend(painter, w, h)

        painter.end()

    def _paint_splat(self, painter, idx, screen_pos):
        sx, sy = screen_pos
        scale = self._scales[idx]
        rot = self._rotations[idx]
        r, g, b = self._colors[idx]
        opacity = self._opacities[idx]
        is_hovered = idx == self._hovered_idx

        # Project covariance onto XY to get 2D ellipse shape
        # Σ₃D = R diag(s²) Rᵀ
        S2 = np.diag(scale ** 2)
        sigma_3d = rot @ S2 @ rot.T

        # Project: take top-left 2×2 submatrix of rotated covariance
        # Apply view rotation first
        ry = self._view_ry
        cy, sy_r = np.cos(ry), np.sin(ry)
        Rx = np.array([[cy, 0, sy_r], [0, 1, 0], [-sy_r, 0, cy]])
        rx = self._view_rx
        cx, sx_r = np.cos(rx), np.sin(rx)
        Rv = Rx @ np.array([[1, 0, 0], [0, cx, -sx_r], [0, sx_r, cx]])

        view_sigma = Rv @ sigma_3d @ Rv.T
        sigma_2d = view_sigma[:2, :2]

        # Eigendecompose Σ₂D → ellipse parameters
        try:
            eigvals, eigvecs = np.linalg.eigh(sigma_2d)
            eigvals = np.maximum(eigvals, 0.001)
        except:
            eigvals = np.array([scale[0]**2, scale[1]**2])
            eigvecs = np.eye(2)

        # Semi-axes in pixels
        zoom_factor = self._zoom * (min(self.width(), self.height()) - 160) / 35
        rx_px = np.sqrt(eigvals[1]) * zoom_factor * 3.0  # 3σ coverage
        ry_px = np.sqrt(eigvals[0]) * zoom_factor * 3.0

        # Rotation angle from eigenvector
        angle = np.degrees(np.arctan2(eigvecs[1, 1], eigvecs[0, 1]))

        # Size the gradient ellipse
        glow_rx = rx_px * 1.8
        glow_ry = ry_px * 1.8

        # --- Glow pass ---
        base_color = QColor(int(r * 255), int(g * 255), int(b * 255))
        glow = QRadialGradient(QPointF(sx, sy), max(glow_rx, glow_ry))
        glow.setColorAt(0, QColor(base_color.red(), base_color.green(), base_color.blue(), int(opacity * 90)))
        glow.setColorAt(0.3, QColor(base_color.red(), base_color.green(), base_color.blue(), int(opacity * 50)))
        glow.setColorAt(0.6, QColor(base_color.red(), base_color.green(), base_color.blue(), int(opacity * 20)))
        glow.setColorAt(1.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glow))
        painter.save()
        painter.translate(sx, sy)
        painter.rotate(angle)
        painter.scale(1.0, glow_ry / max(glow_rx, 1))
        painter.drawEllipse(QPointF(0, 0), glow_rx, glow_rx)
        painter.restore()

        # --- Core pass — tighter, brighter ---
        core = QRadialGradient(QPointF(sx, sy), max(rx_px, ry_px))
        bright = base_color.lighter(130 if not is_hovered else 160)
        core.setColorAt(0.0, QColor(bright.red(), bright.green(), bright.blue(), int(opacity * 255)))
        core.setColorAt(0.15, QColor(bright.red(), bright.green(), bright.blue(), int(opacity * 220)))
        core.setColorAt(0.35, QColor(base_color.red(), base_color.green(), base_color.blue(), int(opacity * 160)))
        core.setColorAt(0.6, QColor(base_color.red(), base_color.green(), base_color.blue(), int(opacity * 70)))
        core.setColorAt(0.85, QColor(base_color.red(), base_color.green(), base_color.blue(), int(opacity * 20)))
        core.setColorAt(1.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 0))

        painter.setBrush(QBrush(core))
        painter.save()
        painter.translate(sx, sy)
        painter.rotate(angle)
        painter.scale(1.0, ry_px / max(rx_px, 1))
        painter.drawEllipse(QPointF(0, 0), rx_px, rx_px)
        painter.restore()

        # --- Label ---
        if is_hovered:
            node_list = list(self._nodes.values())
            if idx < len(node_list):
                meta = node_list[idx].get("metadata", {})
                label = meta.get("label", "")
                if label:
                    painter.setPen(QPen(QColor(Colors.TEXT)))
                    painter.setFont(QFont("sans-serif", 9))
                    painter.drawText(int(sx + rx_px + 6), int(sy - 4), label)

    def _paint_connections(self, painter, projected):
        mode = self._conn_mode
        nodes = list(self._nodes.values())
        id_to_idx = {n["id"]: i for i, n in enumerate(nodes)}
        drawn = set()

        for i, node in enumerate(nodes):
            conns = node.get("connections", [])
            if not conns:
                continue
            if mode == "Nearest 5":
                conns = sorted(conns, key=lambda c: c.get("score", 0), reverse=True)[:5]
            elif mode == "Nearest 10":
                conns = sorted(conns, key=lambda c: c.get("score", 0), reverse=True)[:10]
            elif mode == "Above threshold":
                conns = [c for c in conns if c.get("score", 0) > 0.7]
            elif mode == "None":
                return

            for conn in conns:
                j = id_to_idx.get(conn.get("id"))
                if j is None or j <= i:
                    continue
                edge = (i, j)
                if edge in drawn:
                    continue
                drawn.add(edge)

                score = conn.get("score", 0.5)
                t = score
                alpha = int((0.1 + 0.4 * t) * 255)
                r = int((0.3 + 0.6 * t) * 255)
                g = int((0.3 + 0.3 * (1 - t) + 0.4 * t) * 255)
                b_c = int((0.8 * (1 - t) + 0.1 * t) * 255)

                painter.setPen(QPen(QColor(r, g, b_c, alpha), 1.0 + score * 2))
                painter.drawLine(
                    QPointF(projected[i][0], projected[i][1]),
                    QPointF(projected[j][0], projected[j][1])
                )

    def _paint_selection_ring(self, painter, idx, screen_pos):
        sx, sy = screen_pos
        scale = self._scales[idx]
        zoom_factor = self._zoom * (min(self.width(), self.height()) - 160) / 35
        r_px = max(scale) * zoom_factor * 4.0

        pen = QPen(QColor(Colors.ACCENT), 2.5)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(sx, sy), r_px, r_px)

    def _paint_legend(self, painter, w, h):
        painter.setPen(QPen(QColor(Colors.TEXT_DIM)))
        painter.setFont(QFont("monospace", 8))
        painter.drawText(10, h - 10,
            f"α(x) = α₀·exp(-½·d²_M)  |  {len(self._positions)} splats  |  "
            f"Drag: rotate  Shift+Drag: pan  Scroll: zoom")

    def set_connection_mode(self, mode):
        self._conn_mode = mode
        self.update()

    def _compute_connections(self):
        self._conn_mode = "Nearest 5"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ShiftModifier:
                self._pan_start = (event.position().x(), event.position().y())
            else:
                self._drag_start = (event.position().x(), event.position().y())
        elif event.button() == Qt.RightButton:
            # Click to select nearest splat
            self._select_at(event.position())

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self._drag_start and not (event.modifiers() & Qt.ShiftModifier):
            dx = pos.x() - self._drag_start[0]
            dy = pos.y() - self._drag_start[1]
            self._view_ry += dx * 0.005
            self._view_rx += dy * 0.005
            self._drag_start = (pos.x(), pos.y())
            self.update()
        elif self._pan_start and (event.modifiers() & Qt.ShiftModifier):
            dx = pos.x() - self._pan_start[0]
            dy = pos.y() - self._pan_start[1]
            scale = 35 / (min(self.width(), self.height()) - 160) / self._zoom
            self._pan_offset[0] += dx * scale
            self._pan_offset[1] -= dy * scale
            self._pan_start = (pos.x(), pos.y())
            self.update()
        else:
            # Hover detection
            self._hover_at(pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = None
            self._pan_start = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self._zoom *= 1.1 if delta > 0 else 0.9
        self._zoom = max(0.2, min(self._zoom, 5.0))
        self.update()

    def _hover_at(self, pos):
        if self._positions is None:
            return
        best, best_d = -1, 30  # pixel threshold
        for i in range(len(self._positions)):
            px, py, _ = self._project(self._positions[i])
            sx, sy = self._to_screen(px, py)
            d = ((pos.x() - sx)**2 + (pos.y() - sy)**2)**0.5
            if d < best_d:
                best_d = d
                best = i
        if best != self._hovered_idx:
            self._hovered_idx = best
            self.update()

    def _select_at(self, pos):
        if self._positions is None:
            return
        best, best_d = -1, 40
        for i in range(len(self._positions)):
            px, py, _ = self._project(self._positions[i])
            sx, sy = self._to_screen(px, py)
            d = ((pos.x() - sx)**2 + (pos.y() - sy)**2)**0.5
            if d < best_d:
                best_d = d
                best = i
        if best >= 0:
            self._selected_idx = best
            keys = list(self._nodes.keys())
            if best < len(keys):
                self.node_clicked.emit(keys[best])
            self.update()


# ---------------------------------------------------------------------------
# Splat3D View — auto-selects GL or 2D canvas
# ---------------------------------------------------------------------------

class Splat3DView(QWidget):
    """Gaussian Splat Explorer — auto-selects GL or QPainter rendering."""

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

        self._gl_items = []
        self._gl_lines = []
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

        self.mode_label = QLabel("")
        self.mode_label.setStyleSheet(f"color: {Colors.ACCENT}; font-size: 10px; font-weight: 600;")
        tb.addWidget(self.mode_label)

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

        # Canvas — try GL first, fall back to 2D
        if _GL_OK and not os.environ.get("SPLATSDB_NO_GL"):
            self._init_gl_canvas(layout)
        else:
            self._init_2d_canvas(layout)

        # Info bar
        self.info_bar = QLabel("Click a splat to inspect | Drag to rotate | Shift+Drag to pan | Scroll to zoom")
        self.info_bar.setStyleSheet(f"""
            color: {Colors.TEXT_DIM}; font-size: 11px; padding: 6px 12px;
            background-color: {Colors.BG_RAISED}; border-top: 1px solid {Colors.BORDER};
        """)
        layout.addWidget(self.info_bar)
        self.setStyleSheet(f"background-color: {Colors.BG};")

    def _init_2d_canvas(self, layout):
        self.canvas = Splat2DCanvas()
        self.canvas.node_clicked.connect(self._on_canvas_select)
        layout.addWidget(self.canvas, stretch=1)
        self.mode_label.setText("2D Projection")
        self._gl_available = False

    def _init_gl_canvas(self, layout):
        try:
            self.gl_widget = gl.GLViewWidget()
            self.gl_widget.setBackgroundColor(pg.mkColor(Colors.BG))
            self.gl_widget.setCameraPosition(distance=40, elevation=25, azimuth=45)
            self.gl_widget.setMinimumHeight(400)

            grid = gl.GLGridItem()
            grid.setSize(50, 50, 1)
            grid.setSpacing(5, 5, 5)
            grid.setColor(pg.mkColor(Colors.BORDER))
            self.gl_widget.addItem(grid)

            for clr, d in [
                (pg.mkColor("#ef4444"), np.array([[0,0,0],[25,0,0]])),
                (pg.mkColor("#22c55e"), np.array([[0,0,0],[0,25,0]])),
                (pg.mkColor("#3b82f6"), np.array([[0,0,0],[0,0,25]])),
            ]:
                self.gl_widget.addItem(gl.GLLinePlotItem(pos=d, color=clr, width=2, antialias=True))

            layout.addWidget(self.gl_widget, stretch=1)
            self.mode_label.setText("3D OpenGL")
            self._gl_available = True
            self.canvas = None
        except Exception:
            self._init_2d_canvas(layout)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def load_nodes(self, nodes: list[dict]):
        if not nodes:
            return

        self._nodes = {n["id"]: n for n in nodes}
        n = len(nodes)

        positions = []
        for node in nodes:
            if "position" in node and len(node["position"]) >= 3:
                positions.append(node["position"][:3])
            elif "vector" in node and len(node["vector"]) >= 3:
                positions.append(node["vector"][:3])
            else:
                positions.append([np.random.uniform(-10, 10) for _ in range(3)])
        self._positions = np.array(positions, dtype=np.float32)

        for dim in range(3):
            col = self._positions[:, dim]
            mn, mx = col.min(), col.max()
            if mx > mn:
                self._positions[:, dim] = (col - mn) / (mx - mn) * 30 - 15

        self._colors = [palette_color(i) for i in range(n)]

        base = self.size_slider.value() / 10.0
        np.random.seed(42)
        scales = []
        for i in range(n):
            if "scale" in nodes[i]:
                scales.append(nodes[i]["scale"][:3])
            else:
                frac = (i * 0.618) % 1.0
                scales.append([
                    base * (0.7 + 0.6 * frac),
                    base * (0.7 + 0.6 * (1 - frac)),
                    base * (0.5 + 0.4 * np.random.random()),
                ])
        self._scales = np.array(scales, dtype=np.float32)

        rotations = []
        for i in range(n):
            if "rotation" in nodes[i]:
                rotations.append(rotation_matrix(*nodes[i]["rotation"][:3]))
            else:
                golden_angle = np.pi * (3 - np.sqrt(5))
                theta = golden_angle * i
                phi = np.arccos(1 - 2 * (i + 0.5) / n)
                rotations.append(rotation_matrix(theta, phi, 0))
        self._rotations = np.array(rotations, dtype=np.float32)

        base_o = self.opacity_slider.value() / 100.0
        self._opacities = np.array(
            [nodes[i].get("opacity", base_o) for i in range(n)], dtype=np.float32
        )

        self._render()

    def _render(self):
        if self._positions is None:
            return

        if self._gl_available:
            self._render_gl()
        elif self.canvas is not None:
            self._render_2d()

        nc = sum(len(n.get("connections", [])) for n in self._nodes.values()) // 2
        self.info_bar.setText(
            f"{len(self._nodes)} Gaussian splats | α = α₀·exp(-½·d²_M) | "
            f"{nc} connections | {'3D GL' if self._gl_available else '2D Projected'}"
        )

    def _render_2d(self):
        self.canvas.set_data(
            self._nodes, self._positions, self._colors,
            self._scales, self._rotations, self._opacities,
        )

    def _render_gl(self):
        # Clear old items
        for items in self._gl_items:
            for it in items:
                try: self.gl_widget.removeItem(it)
                except: pass
        self._gl_items.clear()
        for line in self._gl_lines:
            try: self.gl_widget.removeItem(line)
            except: pass
        self._gl_lines.clear()

        cam_pos = np.array(self.gl_widget.cameraPosition())
        if hasattr(cam_pos, 'x'):
            cam = np.array([cam_pos.x(), cam_pos.y(), cam_pos.z()])
        else:
            cam = np.zeros(3)
        dists = np.linalg.norm(self._positions - cam, axis=1)
        order = np.argsort(-dists)

        for idx in order:
            glow_md, core_md = build_splat_mesh(
                self._positions[idx], self._scales[idx],
                self._rotations[idx], self._colors[idx], self._opacities[idx],
            )
            glow_item = gl.GLMeshItem(meshdata=glow_md, smooth=True, shader='balloon', glOptions='translucent')
            core_item = gl.GLMeshItem(meshdata=core_md, smooth=True, shader='balloon', glOptions='translucent')
            self.gl_widget.addItem(glow_item)
            self.gl_widget.addItem(core_item)
            self._gl_items.append((glow_item, core_item))

        self._draw_gl_connections()

    def _draw_gl_connections(self):
        for line in self._gl_lines:
            try: self.gl_widget.removeItem(line)
            except: pass
        self._gl_lines.clear()

        mode = self.conn_combo.currentText()
        if mode == "None":
            return

        nodes = list(self._nodes.values())
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
                j = id_to_idx.get(conn.get("id"))
                if j is None or j <= i:
                    continue
                score = conn.get("score", 0.5)
                t = score
                alpha = 0.15 + 0.35 * t
                color = (0.3+0.6*t, 0.3+0.3*(1-t)+0.4*t, 0.8*(1-t)+0.1*t, alpha)
                line = gl.GLLinePlotItem(
                    pos=np.array([self._positions[i], self._positions[j]]),
                    color=color, width=1.0+score*2.5, antialias=True,
                )
                self.gl_widget.addItem(line)
                self._gl_lines.append(line)
                edges += 1

    def _on_canvas_select(self, node_id):
        self.select_node(node_id)

    def select_node(self, node_id: str):
        keys = list(self._nodes.keys())
        if node_id not in keys:
            return
        idx = keys.index(node_id)
        node = self._nodes[node_id]
        meta = node.get("metadata", {})
        text = meta.get("text", meta.get("label", node_id))
        self.info_bar.setText(
            f"Selected: {text[:80]}  |  "
            f"{len(node.get('connections', []))} connections  |  "
            f"{len(node.get('files', []))} files"
        )
        self.node_selected.emit(node_id)

        if not self._gl_available and self.canvas is not None:
            self.canvas._selected_idx = idx
            self.canvas.update()

    # Toolbar handlers
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
        self._render()

    def _on_size_changed(self, value):
        if self._scales is None:
            return
        base = value / 10.0
        for i in range(len(self._scales)):
            ratio = self._scales[i] / (self._scales[i].max() + 0.01)
            self._scales[i] = ratio * base
        self._render()

    def _on_opacity_changed(self, value):
        if self._opacities is None:
            return
        self._opacities[:] = value / 100.0
        self._render()

    def _on_connections_changed(self, _):
        if self._nodes:
            if self._gl_available:
                self._draw_gl_connections()
            elif self.canvas is not None:
                self.canvas.set_connection_mode(self.conn_combo.currentText())

    def _reset_camera(self):
        if self._gl_available:
            self.gl_widget.setCameraPosition(distance=40, elevation=25, azimuth=45)
            self.gl_widget.pan(0, 0, 0)
        elif self.canvas is not None:
            self.canvas._view_rx = 0.35
            self.canvas._view_ry = 0.5
            self.canvas._pan_offset = np.zeros(2)
            self.canvas._zoom = 1.0
            self.canvas.update()
