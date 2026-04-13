# SPDX-License-Identifier: GPL-3.0
"""Cluster Distribution View — visualize cluster topology and distributions.

Shows:
- Convex hulls around each cluster (filled with transparency)
- Centroid markers with labels
- Standard deviation rings (1σ, 2σ, 3σ ellipses)
- Inter-cluster connection arcs with strength indicators
- Density heatmaps
- Per-cluster stats panel

Each cluster gets its own color and visual identity.
"""

from __future__ import annotations

import colorsys
import numpy as np
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QFrame, QScrollArea, QSplitter,
    QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient,
    QPainterPath, QRadialGradient, QPolygonF,
)
from PySide6.QtWidgets import QTreeWidgetItem, QTreeWidget, QHeaderView

from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon


def _cluster_color(index: int, total: int) -> QColor:
    """Generate visually distinct colors using golden ratio distribution."""
    hue = (index * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.65, 0.90)
    return QColor(int(r * 255), int(g * 255), int(b * 255))


def _convex_hull(points: np.ndarray) -> np.ndarray:
    """2D convex hull — Andrew's monotone chain."""
    pts = sorted(points.tolist())
    if len(pts) <= 1:
        return np.array(pts)

    def cross(O, A, B):
        return (A[0] - O[0]) * (B[1] - O[1]) - (A[1] - O[1]) * (B[0] - O[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return np.array(lower[:-1] + upper[:-1])


class ClusterCanvas(QWidget):
    """Custom painted canvas showing cluster distributions."""

    cluster_clicked = Signal(int)  # cluster index

    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

        self._positions: Optional[np.ndarray] = None  # (N, 2)
        self._labels: Optional[np.ndarray] = None     # (N,) cluster assignments
        self._n_clusters: int = 0
        self._centroids: Optional[np.ndarray] = None
        self._stds: Optional[np.ndarray] = None       # (K, 2) standard deviations
        self._connections: list[dict] = []             # inter-cluster connections
        self._hovered_cluster: int = -1
        self._selected_cluster: int = -1

        self.show_hulls = True
        self.show_sigma_rings = True
        self.show_centroids = True
        self.show_points = True
        self.show_heatmap = False

    def set_data(self, positions: np.ndarray, labels: np.ndarray, connections: list[dict] = None):
        """Set cluster data.

        Args:
            positions: (N, 2) projected positions
            labels: (N,) cluster assignment per point
            connections: optional inter-cluster connections
        """
        self._positions = positions
        self._labels = labels
        self._n_clusters = len(set(labels))
        self._connections = connections or []

        # Compute centroids and stds
        self._centroids = np.zeros((self._n_clusters, 2))
        self._stds = np.zeros((self._n_clusters, 2))
        for k in range(self._n_clusters):
            mask = labels == k
            if mask.any():
                pts = positions[mask]
                self._centroids[k] = pts.mean(axis=0)
                self._stds[k] = pts.std(axis=0)

        self.update()

    def _to_screen(self, point: np.ndarray, w: int, h: int, margin: int = 60) -> tuple:
        """Transform data coords to screen coords."""
        if self._positions is None:
            return 0, 0
        x_min, y_min = self._positions.min(axis=0)
        x_max, y_max = self._positions.max(axis=0)
        x_range = max(x_max - x_min, 0.01)
        y_range = max(y_max - y_min, 0.01)

        sx = margin + (point[0] - x_min) / x_range * (w - 2 * margin)
        sy = margin + (1.0 - (point[1] - y_min) / y_range) * (h - 2 * margin)  # flip Y
        return sx, sy

    def paintEvent(self, event):
        if self._positions is None or self._labels is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(Colors.BG))

        # Heatmap (optional)
        if self.show_heatmap:
            self._paint_heatmap(painter, w, h)

        # For each cluster
        for k in range(self._n_clusters):
            color = _cluster_color(k, self._n_clusters)
            mask = self._labels == k
            pts = self._positions[mask]
            if len(pts) == 0:
                continue

            screen_pts = np.array([self._to_screen(p, w, h) for p in pts])

            # Convex hull
            if self.show_hulls and len(pts) >= 3:
                hull = _convex_hull(screen_pts)
                if len(hull) >= 3:
                    # Fill
                    fill_color = QColor(color)
                    alpha = 30 if k != self._hovered_cluster and k != self._selected_cluster else 60
                    fill_color.setAlpha(alpha)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(fill_color))

                    path = QPainterPath()
                    path.moveTo(hull[0][0], hull[0][1])
                    for p in hull[1:]:
                        path.lineTo(p[0], p[1])
                    path.closeSubpath()
                    # Expand hull slightly for padding
                    painter.drawPath(path)

                    # Outline
                    outline_color = QColor(color)
                    outline_color.setAlpha(120)
                    pen = QPen(outline_color, 2)
                    pen.setStyle(Qt.DashLine if k != self._selected_cluster else Qt.SolidLine)
                    painter.setPen(pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPath(path)

            # Sigma rings (ellipses around centroid)
            if self.show_sigma_rings and self._centroids is not None:
                cx, cy = self._to_screen(self._centroids[k], w, h)
                sx_range = max(self._stds[k][0], 0.01)
                sy_range = max(self._stds[k][1], 0.01)

                # Scale std to pixels
                full_range = self._positions.max(axis=0) - self._positions.min(axis=0)
                px_scale_x = (w - 120) / max(full_range[0], 0.01)
                px_scale_y = (h - 120) / max(full_range[1], 0.01)

                for sigma_mult, alpha in [(3, 20), (2, 40), (1, 70)]:
                    rx = sx_range * sigma_mult * px_scale_x
                    ry = sy_range * sigma_mult * px_scale_y

                    ring_color = QColor(color)
                    ring_color.setAlpha(alpha)
                    pen = QPen(ring_color, 1.5)
                    pen.setStyle(Qt.DotLine)
                    painter.setPen(pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(int(cx - rx), int(cy - ry), int(2 * rx), int(2 * ry))

            # Points
            if self.show_points:
                point_color = QColor(color)
                point_color.setAlpha(180)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(point_color))
                for sp in screen_pts:
                    size = 4 if k != self._hovered_cluster else 6
                    painter.drawEllipse(int(sp[0] - size // 2), int(sp[1] - size // 2), size, size)

            # Centroid
            if self.show_centroids and self._centroids is not None:
                cx, cy = self._to_screen(self._centroids[k], w, h)

                # Diamond marker
                painter.setPen(QPen(QColor(Colors.BG), 2))
                painter.setBrush(QBrush(color))
                diamond = QPolygonF([
                    __import__('PySide6.QtCore', fromlist=['QPointF']).QPointF(cx, cy - 10),
                    __import__('PySide6.QtCore', fromlist=['QPointF']).QPointF(cx + 8, cy),
                    __import__('PySide6.QtCore', fromlist=['QPointF']).QPointF(cx, cy + 10),
                    __import__('PySide6.QtCore', fromlist=['QPointF']).QPointF(cx - 8, cy),
                ])
                painter.drawPolygon(diamond)

                # Label
                painter.setPen(QPen(QColor(Colors.TEXT)))
                painter.setFont(QFont("sans-serif", 9, QFont.Bold))
                label = f"C{k}" if k >= 0 else "Noise"
                painter.drawText(int(cx + 12), int(cy - 4), label)
                painter.setFont(QFont("sans-serif", 8))
                painter.setPen(QPen(QColor(Colors.TEXT_DIM)))
                painter.drawText(int(cx + 12), int(cy + 10), f"n={mask.sum()}")

        # Inter-cluster connections
        self._paint_connections(painter, w, h)

        painter.end()

    def _paint_heatmap(self, painter: QPainter, w: int, h: int):
        """Render density heatmap in background."""
        if self._positions is None:
            return
        # Simple grid-based density
        grid_size = 40
        x_min, y_min = self._positions.min(axis=0)
        x_max, y_max = self._positions.max(axis=0)

        cell_w = (w - 120) / grid_size
        cell_h = (h - 120) / grid_size

        density = np.zeros((grid_size, grid_size))
        for pt in self._positions:
            gx = int((pt[0] - x_min) / max(x_max - x_min, 0.01) * (grid_size - 1))
            gy = int((1 - (pt[1] - y_min) / max(y_max - y_min, 0.01)) * (grid_size - 1))
            gx = max(0, min(gx, grid_size - 1))
            gy = max(0, min(gy, grid_size - 1))
            density[gy, gx] += 1

        max_d = max(density.max(), 1)
        for gy in range(grid_size):
            for gx in range(grid_size):
                if density[gy, gx] > 0:
                    alpha = int(min(density[gy, gx] / max_d * 80, 80))
                    painter.fillRect(
                        int(60 + gx * cell_w), int(60 + gy * cell_h),
                        int(cell_w) + 1, int(cell_h) + 1,
                        QColor(Colors.ACCENT_RED if hasattr(Colors, 'ACCENT_RED') else 245, 158, 11, alpha),
                    )

    def _paint_connections(self, painter: QPainter, w: int, h: int):
        """Draw inter-cluster connection arcs."""
        if not self._connections or self._centroids is None:
            return

        for conn in self._connections:
            src, dst = conn.get("source", 0), conn.get("target", 0)
            score = conn.get("score", 0)

            if src >= self._n_clusters or dst >= self._n_clusters:
                continue

            p1 = self._to_screen(self._centroids[src], w, h)
            p2 = self._to_screen(self._centroids[dst], w, h)

            # Curved arc
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2 - 20 * (1 - score)

            alpha = int(score * 200)
            pen = QPen(QColor(Colors.TEXT_DIM if score < 0.5 else Colors.ACCENT))
            pen.setWidthF(1.0 + score * 3)
            color = QColor(pen.color())
            color.setAlpha(alpha)
            pen.setColor(color)
            painter.setPen(pen)

            path = QPainterPath()
            path.moveTo(p1[0], p1[1])
            path.quadTo(mid_x, mid_y, p2[0], p2[1])
            painter.drawPath(path)

            # Score label
            if score > 0.6:
                painter.setFont(QFont("monospace", 7))
                painter.setPen(QPen(QColor(Colors.TEXT_DIM)))
                painter.drawText(int(mid_x - 15), int(mid_y - 5), f"{score:.2f}")

    def mouseMoveEvent(self, event):
        """Hover to highlight cluster."""
        if self._centroids is None:
            return
        pos = event.position()
        closest = -1
        min_dist = float('inf')
        for k in range(self._n_clusters):
            cx, cy = self._to_screen(self._centroids[k], self.width(), self.height())
            d = ((pos.x() - cx) ** 2 + (pos.y() - cy) ** 2) ** 0.5
            if d < min_dist and d < 50:
                min_dist = d
                closest = k

        if closest != self._hovered_cluster:
            self._hovered_cluster = closest
            self.update()

    def mousePressEvent(self, event):
        if self._hovered_cluster >= 0:
            self._selected_cluster = self._hovered_cluster
            self.cluster_clicked.emit(self._selected_cluster)
            self.update()


class ClusterStatsPanel(QWidget):
    """Side panel showing per-cluster statistics."""

    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        title = QLabel("CLUSTER STATS")
        title.setStyleSheet(f"color: {Colors.ACCENT}; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(title)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Cluster", "Size", "Spread", "Density"])
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.setAlternatingRowColors(False)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT};
                font-size: 11px;
            }}
            QTreeWidget::item {{ padding: 4px; }}
            QTreeWidget::item:hover {{ background-color: {Colors.BG_RAISED}; }}
            QHeaderView::section {{
                background-color: {Colors.BG_RAISED};
                color: {Colors.TEXT_DIM};
                border: none;
                padding: 4px;
                font-size: 10px;
            }}
        """)
        layout.addWidget(self.tree)
        self.setStyleSheet(f"background-color: {Colors.BG_RAISED};")

    def update_stats(self, labels: np.ndarray, centroids: np.ndarray, stds: np.ndarray):
        self.tree.clear()
        n_clusters = len(centroids)
        for k in range(n_clusters):
            mask = labels == k
            size = int(mask.sum())
            spread = float(np.mean(stds[k]))
            density = size / max(spread ** 2, 0.01)

            color = _cluster_color(k, n_clusters)
            item = QTreeWidgetItem([
                f"● Cluster {k}",
                str(size),
                f"{spread:.3f}",
                f"{density:.1f}",
            ])
            item.setForeground(0, color)
            self.tree.addTopLevelItem(item)


class ClusterView(QWidget):
    """Cluster distribution visualization with stats panel."""

    def __init__(self, signals, state):
        super().__init__()
        self.signals = signals
        self.state = state
        self._nodes: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 8, 12, 8)
        toolbar.setSpacing(10)

        title = QLabel("Cluster Distribution")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 14px; font-weight: 700;")
        toolbar.addWidget(title)

        toolbar.addWidget(QLabel("Projection:"))
        self.proj_combo = QComboBox()
        self.proj_combo.addItems(["PCA", "t-SNE", "First 2 Dims"])
        self.proj_combo.setCurrentText("First 2 Dims")
        self.proj_combo.currentTextChanged.connect(self._rebuild)
        toolbar.addWidget(self.proj_combo)

        toolbar.addWidget(QLabel("Clusters:"))
        self.k_slider = QSlider(Qt.Horizontal)
        self.k_slider.setRange(2, 15)
        self.k_slider.setValue(5)
        self.k_slider.setFixedWidth(80)
        self.k_slider.valueChanged.connect(self._rebuild)
        toolbar.addWidget(self.k_slider)
        self.k_label = QLabel("5")
        self.k_label.setStyleSheet(f"color: {Colors.ACCENT}; font-weight: 700;")
        toolbar.addWidget(self.k_label)

        toolbar.addStretch()

        self.heatmap_btn = QPushButton("Heatmap")
        self.heatmap_btn.setCheckable(True)
        self.heatmap_btn.toggled.connect(self._toggle_heatmap)
        toolbar.addWidget(self.heatmap_btn)

        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar)
        toolbar_widget.setStyleSheet(
            f"background-color: {Colors.BG_RAISED}; border-bottom: 1px solid {Colors.BORDER};"
        )
        layout.addWidget(toolbar_widget)

        # Content: canvas + stats
        splitter = QSplitter(Qt.Horizontal)
        self.canvas = ClusterCanvas()
        splitter.addWidget(self.canvas)
        self.stats_panel = ClusterStatsPanel()
        splitter.addWidget(self.stats_panel)
        splitter.setSizes([700, 280])
        layout.addWidget(splitter, stretch=1)

        self.setStyleSheet(f"background-color: {Colors.BG};")

    def load_nodes(self, nodes: list[dict]):
        self._nodes = nodes
        self._rebuild()

    def _rebuild(self):
        if not self._nodes:
            return

        self.k_label.setText(str(self.k_slider.value()))

        # Extract vectors
        vectors = []
        for n in self._nodes:
            v = n.get("vector", n.get("position", []))
            if len(v) < 2:
                v = list(v) + [0.0] * (2 - len(v))
            vectors.append(v)

        mat = np.array(vectors, dtype=np.float32)

        # Project to 2D
        proj = self.proj_combo.currentText()
        if proj == "First 2 Dims":
            positions = mat[:, :2]
        elif proj == "PCA":
            try:
                from sklearn.decomposition import PCA
                positions = PCA(n_components=2).fit_transform(mat)
            except ImportError:
                positions = mat[:, :2]
        else:
            try:
                from sklearn.manifold import TSNE
                positions = TSNE(n_components=2, perplexity=min(30, len(mat) - 1)).fit_transform(mat)
            except ImportError:
                positions = mat[:, :2]

        positions = positions.astype(np.float32)

        # Cluster
        k = self.k_slider.value()
        try:
            from sklearn.cluster import KMeans
            labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(mat)
        except ImportError:
            # Fallback: simple assignment by first dimension quantiles
            labels = np.digitize(mat[:, 0], np.linspace(mat[:, 0].min(), mat[:, 0].max(), k)) - 1

        # Inter-cluster connections (average pairwise scores)
        connections = self._compute_cluster_connections(labels)

        self.canvas.set_data(positions, labels, connections)

        # Stats
        centroids = np.zeros((k, 2))
        stds = np.zeros((k, 2))
        for c in range(k):
            mask = labels == c
            if mask.any():
                centroids[c] = positions[mask].mean(axis=0)
                stds[c] = positions[mask].std(axis=0)
        self.stats_panel.update_stats(labels, centroids, stds)

    def _compute_cluster_connections(self, labels: np.ndarray) -> list[dict]:
        """Compute average inter-cluster affinity from node connections."""
        n_clusters = len(set(labels))
        affinity = np.zeros((n_clusters, n_clusters))
        counts = np.zeros((n_clusters, n_clusters))

        node_ids = list(self._nodes) if isinstance(self._nodes, dict) else [n.get("id", str(i)) for i, n in enumerate(self._nodes)]
        id_to_idx = {nid: i for i, nid in enumerate(node_ids)}

        for i, node in enumerate(self._nodes):
            ci = labels[i]
            for conn in node.get("connections", []):
                j = id_to_idx.get(conn.get("id"))
                if j is not None and j < len(labels):
                    cj = labels[j]
                    score = conn.get("score", 0)
                    affinity[ci, cj] += score
                    counts[ci, cj] += 1

        connections = []
        for i in range(n_clusters):
            for j in range(i + 1, n_clusters):
                if counts[i, j] > 0:
                    connections.append({
                        "source": i, "target": j,
                        "score": affinity[i, j] / counts[i, j],
                    })

        return connections

    def _toggle_heatmap(self, on: bool):
        self.canvas.show_heatmap = on
        self.canvas.update()

    def get_params(self) -> list:
        return [
            {"name": "n_clusters", "label": "Clusters", "type": "spin", "min": 2, "max": 15, "default": 5},
            {"name": "projection", "label": "Projection", "type": "combo", "options": ["PCA", "t-SNE", "First 2 Dims"]},
        ]
