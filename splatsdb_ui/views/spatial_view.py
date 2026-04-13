# SPDX-License-Identifier: GPL-3.0
"""Spatial Architecture Generator — parametric floor plan from vector topology.

Transforms vector space topology into navigable architectural space:
- Clusters → Rooms (size proportional to member count)
- Inter-cluster connections → Corridors (width proportional to affinity)
- High-affinity cluster groups → Wings (labeled sections)
- Hub nodes → Lobbies / junction rooms

Interactive parameters control the generated layout.
Click a room to inspect its contents.
"""

from __future__ import annotations

import colorsys
import numpy as np
from typing import Optional
from collections import defaultdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QFrame, QSplitter, QScrollArea,
    QSizePolicy, QToolBar,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QPainterPath, QLinearGradient, QRadialGradient,
)

from splatsdb_ui.utils.theme import Colors
from splatsdb_ui.utils.icons import icon


def _wing_color(index: int) -> QColor:
    hue = (index * 0.276393202250021 + 0.1) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.35, 0.35)
    return QColor(int(r * 255), int(g * 255), int(b * 255))


def _room_color(index: int) -> QColor:
    hue = (index * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.55, 0.85)
    return QColor(int(r * 255), int(g * 255), int(b * 255))


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Room:
    """A room in the spatial layout."""
    def __init__(self, rid: int, label: str, size: int, color: QColor,
                 members: list[dict], wing: int = -1):
        self.id = rid
        self.label = label
        self.size = size  # member count
        self.color = color
        self.members = members
        self.wing = wing  # wing assignment
        self.x = 0.0
        self.y = 0.0
        self.width = 0.0
        self.height = 0.0

    @property
    def rect(self):
        return (self.x, self.y, self.width, self.height)

    def contains(self, px, py):
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)


class Corridor:
    """A corridor connecting two rooms."""
    def __init__(self, room_a: int, room_b: int, strength: float):
        self.room_a = room_a
        self.room_b = room_b
        self.strength = strength  # 0..1


class Wing:
    """A wing grouping multiple rooms."""
    def __init__(self, wid: int, label: str, color: QColor):
        self.id = wid
        self.label = label
        self.color = color
        self.rooms: list[int] = []


# ---------------------------------------------------------------------------
# Layout engine
# ---------------------------------------------------------------------------

class SpatialLayoutEngine:
    """Generates architectural floor plan from cluster topology."""

    def __init__(self):
        self.rooms: list[Room] = []
        self.corridors: list[Corridor] = []
        self.wings: list[Wing] = []

        self.room_scale = 1.0       # size multiplier
        self.corridor_width = 12     # pixels
        self.wing_threshold = 0.5    # min affinity to group into wing
        self.layout_mode = "force"   # force | circular | grid
        self.padding = 30            # room padding

    def generate(self, nodes: list[dict], n_clusters: int = 5):
        """Generate floor plan from nodes."""
        if not nodes:
            return

        # 1. Cluster nodes
        vectors = []
        for n in nodes:
            v = n.get("vector", n.get("position", []))
            vectors.append(v[:min(len(v), 64)] if v else [0.0])
        mat = np.array(vectors, dtype=np.float32)

        # Pad to same length
        max_len = max(len(v) for v in vectors)
        padded = np.zeros((len(vectors), max_len), dtype=np.float32)
        for i, v in enumerate(vectors):
            padded[i, :len(v)] = v[:max_len]

        try:
            from sklearn.cluster import KMeans
            labels = KMeans(n_clusters=n_clusters, n_init=10, random_state=42).fit_predict(padded)
        except ImportError:
            labels = np.digitize(padded[:, 0], np.linspace(padded[:, 0].min(), padded[:, 0].max(), n_clusters)) - 1

        # 2. Create rooms from clusters
        cluster_members = defaultdict(list)
        for i, label in enumerate(labels):
            cluster_members[int(label)].append(nodes[i])

        self.rooms = []
        for k in range(n_clusters):
            members = cluster_members.get(k, [])
            meta = members[0].get("metadata", {}) if members else {}
            label = meta.get("category", meta.get("label", f"Room {k}"))
            color = _room_color(k)

            room = Room(
                rid=k,
                label=label,
                size=len(members),
                color=color,
                members=members,
            )
            self.rooms.append(room)

        # 3. Compute inter-cluster affinity
        node_ids = [n.get("id", str(i)) for i, n in enumerate(nodes)]
        id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
        affinity = np.zeros((n_clusters, n_clusters))

        for i, node in enumerate(nodes):
            ci = labels[i]
            for conn in node.get("connections", []):
                j = id_to_idx.get(conn.get("id"))
                if j is not None and j < len(labels):
                    cj = labels[j]
                    affinity[ci, cj] += conn.get("score", 0)

        # Normalize
        for i in range(n_clusters):
            for j in range(n_clusters):
                if i != j:
                    affinity[i, j] /= max(min(self.rooms[i].size, self.rooms[j].size), 1)

        # 4. Create corridors
        self.corridors = []
        for i in range(n_clusters):
            for j in range(i + 1, n_clusters):
                if affinity[i, j] > 0.2:
                    self.corridors.append(Corridor(i, j, min(affinity[i, j], 1.0)))

        # 5. Create wings (groups of highly connected rooms)
        self.wings = self._detect_wings(affinity, n_clusters)

        # 6. Layout
        self._compute_room_sizes()
        self._layout_rooms()

    def _detect_wings(self, affinity: np.ndarray, n: int) -> list[Wing]:
        """Group rooms into wings based on affinity."""
        # Simple: use union-find to merge rooms with affinity > threshold
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            a, b = find(a), find(b)
            if a != b:
                parent[a] = b

        for i in range(n):
            for j in range(i + 1, n):
                if affinity[i, j] > self.wing_threshold:
                    union(i, j)

        # Group
        groups = defaultdict(list)
        for i in range(n):
            groups[find(i)].append(i)

        wings = []
        wing_idx = 0
        for root, members in groups.items():
            if len(members) >= 2:
                w = Wing(wing_idx, f"Wing {chr(65 + wing_idx)}", _wing_color(wing_idx))
                w.rooms = members
                wings.append(w)
                for rid in members:
                    self.rooms[rid].wing = wing_idx
                wing_idx += 1

        return wings

    def _compute_room_sizes(self):
        """Compute room dimensions based on member count."""
        for room in self.rooms:
            area = max(room.size, 1) * self.room_scale * 400  # px² per member
            # Keep aspect ratio reasonable
            side = area ** 0.5
            room.width = side * (1.0 + (room.size % 3) * 0.1) + self.padding * 2
            room.height = side * 0.8 + self.padding * 2

    def _layout_rooms(self):
        """Place rooms according to layout algorithm."""
        if self.layout_mode == "force":
            self._layout_force()
        elif self.layout_mode == "circular":
            self._layout_circular()
        elif self.layout_mode == "grid":
            self._layout_grid()

    def _layout_force(self):
        """Force-directed layout: rooms repel, corridors attract."""
        n = len(self.rooms)
        if n == 0:
            return

        # Initialize positions
        pos = np.random.uniform(0, 200, (n, 2)).astype(np.float64)

        # Build adjacency
        adj = defaultdict(list)
        for c in self.corridors:
            adj[c.room_a].append((c.room_b, c.strength))
            adj[c.room_b].append((c.room_a, c.strength))

        for iteration in range(200):
            forces = np.zeros((n, 2))

            # Repulsion (all pairs)
            for i in range(n):
                for j in range(i + 1, n):
                    diff = pos[i] - pos[j]
                    dist = max(np.linalg.norm(diff), 1.0)
                    # Repulsion inversely proportional to dist²
                    force = diff / dist * (5000 / (dist * dist))
                    forces[i] += force
                    forces[j] -= force

            # Attraction (connected pairs)
            for c in self.corridors:
                diff = pos[c.room_b] - pos[c.room_a]
                dist = max(np.linalg.norm(diff), 1.0)
                force = diff * 0.05 * c.strength
                forces[c.room_a] += force
                forces[c.room_b] -= force

            # Wing cohesion
            for wing in self.wings:
                if len(wing.rooms) < 2:
                    continue
                center = pos[wing.rooms].mean(axis=0)
                for rid in wing.rooms:
                    forces[rid] += (center - pos[rid]) * 0.1

            # Apply with damping
            damping = max(0.1, 1.0 - iteration / 200)
            pos += forces * damping * 0.1

        # Normalize to [50, 800] range
        for dim in range(2):
            col = pos[:, dim]
            mn, mx = col.min(), col.max()
            if mx > mn:
                pos[:, dim] = (col - mn) / (mx - mn) * 600 + 80

        for i, room in enumerate(self.rooms):
            room.x = pos[i, 0]
            room.y = pos[i, 1]

    def _layout_circular(self):
        """Arrange rooms in a circle."""
        n = len(self.rooms)
        cx, cy = 400, 350
        radius = min(cx, cy) * 0.7

        for i, room in enumerate(self.rooms):
            angle = 2 * np.pi * i / n - np.pi / 2
            room.x = cx + radius * np.cos(angle) - room.width / 2
            room.y = cy + radius * np.sin(angle) - room.height / 2

    def _layout_grid(self):
        """Arrange rooms in a grid."""
        n = len(self.rooms)
        cols = int(np.ceil(np.sqrt(n)))
        spacing_x = 250
        spacing_y = 200

        for i, room in enumerate(self.rooms):
            row, col = divmod(i, cols)
            room.x = col * spacing_x + 50
            room.y = row * spacing_y + 50


# ---------------------------------------------------------------------------
# Spatial canvas
# ---------------------------------------------------------------------------

class SpatialCanvas(QWidget):
    """Renders the architectural floor plan."""

    room_clicked = Signal(int)  # room id

    def __init__(self):
        super().__init__()
        self.setMinimumSize(700, 500)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

        self.engine = SpatialLayoutEngine()
        self._hovered_room: int = -1
        self._selected_room: int = -1

        # Visualization toggles
        self.show_room_labels = True
        self.show_member_count = True
        self.show_corridors = True
        self.show_wing_borders = True
        self.show_flow = False

    def generate(self, nodes: list[dict], n_clusters: int = 5):
        self.engine.generate(nodes, n_clusters)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background — dark blueprint
        bg = QColor(Colors.BG)
        painter.fillRect(0, 0, w, h, bg)

        # Subtle grid
        painter.setPen(QPen(QColor(Colors.BORDER + "40" if not Colors.BORDER.startswith("#") else Colors.BORDER), 0.5))
        for x in range(0, w, 30):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, 30):
            painter.drawLine(0, y, w, y)

        # Title
        painter.setPen(QPen(QColor(Colors.TEXT_DIM)))
        painter.setFont(QFont("sans-serif", 8))
        painter.drawText(10, h - 8, "Spatial Architecture Generator — Floor Plan View")

        # Wings (background grouping)
        if self.show_wing_borders:
            self._paint_wings(painter)

        # Corridors
        if self.show_corridors:
            self._paint_corridors(painter)

        # Flow visualization (optional)
        if self.show_flow:
            self._paint_flow(painter)

        # Rooms
        self._paint_rooms(painter)

        painter.end()

    def _paint_wings(self, painter: QPainter):
        for wing in self.engine.wings:
            if len(wing.rooms) < 2:
                continue

            # Compute bounding rect of all rooms in wing
            rooms = [self.engine.rooms[rid] for rid in wing.rooms]
            x_min = min(r.x for r in rooms) - 25
            y_min = min(r.y for r in rooms) - 25
            x_max = max(r.x + r.width for r in rooms) + 25
            y_max = max(r.y + r.height for r in rooms) + 25

            # Wing background
            wing_bg = QColor(wing.color)
            wing_bg.setAlpha(40)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(wing_bg))
            painter.drawRoundedRect(int(x_min), int(y_min),
                                    int(x_max - x_min), int(y_max - y_min), 12, 12)

            # Wing border
            wing_border = QColor(wing.color)
            wing_border.setAlpha(100)
            pen = QPen(wing_border, 2, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(int(x_min), int(y_min),
                                    int(x_max - x_min), int(y_max - y_min), 12, 12)

            # Wing label
            painter.setPen(QPen(QColor(wing.color).lighter(150)))
            painter.setFont(QFont("sans-serif", 11, QFont.Bold))
            painter.drawText(int(x_min + 10), int(y_min + 18), wing.label)

    def _paint_corridors(self, painter: QPainter):
        for corr in self.engine.corridors:
            if corr.room_a >= len(self.engine.rooms) or corr.room_b >= len(self.engine.rooms):
                continue

            ra = self.engine.rooms[corr.room_a]
            rb = self.engine.rooms[corr.room_b]

            # Center points
            ax = ra.x + ra.width / 2
            ay = ra.y + ra.height / 2
            bx = rb.x + rb.width / 2
            by = rb.y + rb.height / 2

            # Corridor width based on strength
            cw = self.engine.corridor_width * (0.5 + corr.strength)

            # Draw corridor as wide path
            color = QColor(Colors.TEXT_DIM)
            color.setAlpha(int(40 + corr.strength * 80))
            painter.setPen(QPen(color, cw, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(int(ax), int(ay), int(bx), int(by))

            # Connection strength indicator (small dot at midpoint)
            mx, my = (ax + bx) / 2, (ay + by) / 2
            dot_color = QColor(Colors.ACCENT)
            dot_color.setAlpha(int(corr.strength * 200))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(int(mx - 3), int(my - 3), 6, 6)

    def _paint_flow(self, painter: QPainter):
        """Draw animated flow particles along corridors."""
        import time
        t = time.time() % 4.0  # 4-second cycle

        for corr in self.engine.corridors:
            if corr.room_a >= len(self.engine.rooms) or corr.room_b >= len(self.engine.rooms):
                continue

            ra = self.engine.rooms[corr.room_a]
            rb = self.engine.rooms[corr.room_b]

            ax, ay = ra.x + ra.width / 2, ra.y + ra.height / 2
            bx, by = rb.x + rb.width / 2, rb.y + rb.height / 2

            # Multiple particles per corridor
            n_particles = max(1, int(corr.strength * 5))
            for p in range(n_particles):
                phase = (t / 4.0 + p / n_particles) % 1.0
                px = ax + (bx - ax) * phase
                py = ay + (by - ay) * phase

                alpha = int(255 * (1 - abs(phase - 0.5) * 2))  # fade at ends
                pc = QColor(Colors.ACCENT)
                pc.setAlpha(alpha)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(pc))
                painter.drawEllipse(int(px - 2), int(py - 2), 4, 4)

    def _paint_rooms(self, painter: QPainter):
        for room in self.engine.rooms:
            x, y, w, h = room.x, room.y, room.width, room.height

            # Room shadow
            shadow = QColor(0, 0, 0, 40)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(shadow))
            painter.drawRoundedRect(int(x + 3), int(y + 3), int(w), int(h), 8, 8)

            # Room fill
            fill = QColor(room.color)
            is_hovered = room.id == self._hovered_room
            is_selected = room.id == self._selected_room

            if is_selected:
                fill = fill.lighter(140)
            elif is_hovered:
                fill = fill.lighter(120)

            fill.setAlpha(200 if is_selected or is_hovered else 160)

            # Gradient fill for depth
            gradient = QLinearGradient(x, y, x, y + h)
            gradient.setColorAt(0, fill.lighter(110))
            gradient.setColorAt(1, fill.darker(110))
            painter.setBrush(QBrush(gradient))

            # Border
            border = QColor(room.color)
            border.setAlpha(255 if is_selected else 180)
            pen_width = 2.5 if is_selected else 1.5
            painter.setPen(QPen(border, pen_width))
            painter.drawRoundedRect(int(x), int(y), int(w), int(h), 8, 8)

            # Room label
            if self.show_room_labels:
                painter.setPen(QPen(QColor(Colors.BG)))
                painter.setFont(QFont("sans-serif", 10, QFont.Bold))
                text = room.label[:20]
                painter.drawText(int(x + 8), int(y + 20), text)

            # Member count
            if self.show_member_count:
                painter.setPen(QPen(QColor(Colors.TEXT_DIM)))
                painter.setFont(QFont("sans-serif", 9))
                painter.drawText(int(x + 8), int(y + 36), f"{room.size} splats")

            # Wing badge
            if room.wing >= 0 and room.wing < len(self.engine.wings):
                wing = self.engine.wings[room.wing]
                badge_color = QColor(wing.color).lighter(150)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(badge_color))
                painter.drawEllipse(int(x + w - 20), int(y + 5), 14, 14)
                painter.setPen(QPen(QColor(Colors.BG)))
                painter.setFont(QFont("sans-serif", 7, QFont.Bold))
                painter.drawText(int(x + w - 18), int(y + 15), wing.label[-1])

    def mouseMoveEvent(self, event):
        pos = event.position()
        for room in self.engine.rooms:
            if room.contains(pos.x(), pos.y()):
                if self._hovered_room != room.id:
                    self._hovered_room = room.id
                    self.setCursor(Qt.PointingHandCursor)
                    self.update()
                return
        if self._hovered_room >= 0:
            self._hovered_room = -1
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def mousePressEvent(self, event):
        if self._hovered_room >= 0:
            self._selected_room = self._hovered_room
            self.room_clicked.emit(self._selected_room)
            self.update()


# ---------------------------------------------------------------------------
# Parameter panel
# ---------------------------------------------------------------------------

class SpatialParamPanel(QWidget):
    """Controls for the spatial architecture generator."""

    generate_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(260)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel("ARCHITECTURE")
        title.setStyleSheet(f"color: {Colors.ACCENT}; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(title)

        # Layout mode
        layout.addWidget(QLabel("Layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Force-directed", "Circular", "Grid"])
        self.layout_combo.setStyleSheet(f"color: {Colors.TEXT}; background: {Colors.BG}; border: 1px solid {Colors.BORDER}; padding: 4px;")
        layout.addWidget(self.layout_combo)

        # Clusters
        layout.addWidget(QLabel("Rooms (clusters):"))
        self.k_slider = QSlider(Qt.Horizontal)
        self.k_slider.setRange(2, 12)
        self.k_slider.setValue(5)
        layout.addWidget(self.k_slider)
        self.k_label = QLabel("5")
        self.k_label.setStyleSheet(f"color: {Colors.ACCENT};")
        layout.addWidget(self.k_label)
        self.k_slider.valueChanged.connect(lambda v: self.k_label.setText(str(v)))

        # Room scale
        layout.addWidget(QLabel("Room scale:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(50, 200)
        self.scale_slider.setValue(100)
        layout.addWidget(self.scale_slider)

        # Corridor width
        layout.addWidget(QLabel("Corridor width:"))
        self.corr_slider = QSlider(Qt.Horizontal)
        self.corr_slider.setRange(4, 30)
        self.corr_slider.setValue(12)
        layout.addWidget(self.corr_slider)

        # Wing threshold
        layout.addWidget(QLabel("Wing threshold:"))
        self.wing_slider = QSlider(Qt.Horizontal)
        self.wing_slider.setRange(10, 90)
        self.wing_slider.setValue(50)
        layout.addWidget(self.wing_slider)

        # Toggles
        self.flow_cb = QPushButton("Show Flow")
        self.flow_cb.setCheckable(True)
        layout.addWidget(self.flow_cb)

        # Generate button
        gen_btn = QPushButton("Regenerate")
        gen_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT}; color: {Colors.BG};
                border: none; border-radius: 6px; padding: 8px; font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT}CC; }}
        """)
        gen_btn.clicked.connect(self.generate_requested.emit)
        layout.addWidget(gen_btn)

        layout.addStretch()

        # Stats
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 10px;")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)

        self.setStyleSheet(f"""
            background-color: {Colors.BG_RAISED};
            QLabel {{ color: {Colors.TEXT}; font-size: 11px; }}
        """)


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------

class SpatialView(QWidget):
    """Spatial Architecture Generator — parametric floor plan from vector topology."""

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

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(12, 8, 12, 8)
        title = QLabel("Spatial Architecture")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 14px; font-weight: 700;")
        header.addWidget(title)

        info = QLabel("Clusters → Rooms | Connections → Corridors | Groups → Wings")
        info.setStyleSheet(f"color: {Colors.TEXT_DIM}; font-size: 11px;")
        header.addWidget(info)
        header.addStretch()

        header_widget = QWidget()
        header_widget.setLayout(header)
        header_widget.setStyleSheet(
            f"background-color: {Colors.BG_RAISED}; border-bottom: 1px solid {Colors.BORDER};"
        )
        layout.addWidget(header_widget)

        # Content: canvas + params
        splitter = QSplitter(Qt.Horizontal)
        self.canvas = SpatialCanvas()
        splitter.addWidget(self.canvas)
        self.params = SpatialParamPanel()
        splitter.addWidget(self.params)
        splitter.setSizes([700, 260])
        layout.addWidget(splitter, stretch=1)

        # Connect
        self.params.generate_requested.connect(self._regenerate)
        self.canvas.room_clicked.connect(self._on_room_clicked)

        self.setStyleSheet(f"background-color: {Colors.BG};")

    def load_nodes(self, nodes: list[dict]):
        self._nodes = nodes
        self._regenerate()

    def _regenerate(self):
        if not self._nodes:
            return

        # Read params
        mode_map = {"Force-directed": "force", "Circular": "circular", "Grid": "grid"}
        self.canvas.engine.layout_mode = mode_map.get(self.params.layout_combo.currentText(), "force")
        self.canvas.engine.corridor_width = self.params.corr_slider.value()
        self.canvas.engine.wing_threshold = self.params.wing_slider.value() / 100.0
        self.canvas.engine.room_scale = self.params.scale_slider.value() / 100.0
        self.canvas.show_flow = self.params.flow_cb.isChecked()

        n_clusters = self.params.k_slider.value()
        self.canvas.generate(self._nodes, n_clusters)

        # Update stats
        n_rooms = len(self.canvas.engine.rooms)
        n_corridors = len(self.canvas.engine.corridors)
        n_wings = len(self.canvas.engine.wings)
        self.params.stats_label.setText(
            f"Generated: {n_rooms} rooms, {n_corridors} corridors, {n_wings} wings\n"
            f"Layout: {self.canvas.engine.layout_mode}"
        )

    def _on_room_clicked(self, room_id: int):
        if room_id < len(self.canvas.engine.rooms):
            room = self.canvas.engine.rooms[room_id]
            self.signals.status_message.emit(
                f"Room: {room.label} | {room.size} splats | Wing: {room.wing}"
            )
