# SPDX-License-Identifier: GPL-3.0
"""Main application window — composed from mixins (EZ-CorridorKey pattern).

The MainWindow delegates all behavior to mixins, keeping this file as a
thin composition root. Each mixin handles one concern (file ops, search,
views, settings, etc.) and accesses shared state via self.app_state.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStackedWidget, QStatusBar,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QKeySequence, QShortcut

from splatsdb_ui.utils.state import AppState
from splatsdb_ui.utils.signals import SignalBus
from splatsdb_ui.widgets.status_bar import SplatsDBStatusBar
from splatsdb_ui.widgets.search_bar import GlobalSearchBar
from splatsdb_ui.widgets.param_panel import ParamPanel
from splatsdb_ui.widgets.io_tray import IOTray
from splatsdb_ui.widgets.job_queue import JobQueuePanel

from splatsdb_ui.views.welcome_view import WelcomeView
from splatsdb_ui.views.search_view import SearchView
from splatsdb_ui.views.collections_view import CollectionsView
from splatsdb_ui.views.graph_view import GraphView
from splatsdb_ui.views.spatial_view import SpatialView
from splatsdb_ui.views.cluster_view import ClusterView
from splatsdb_ui.views.benchmark_view import BenchmarkView
from splatsdb_ui.views.ocr_view import OCRView

# Mixins
from splatsdb_ui.mixins.file_mixin import FileMixin
from splatsdb_ui.mixins.search_mixin import SearchMixin
from splatsdb_ui.mixins.view_mixin import ViewMixin
from splatsdb_ui.mixins.edit_mixin import EditMixin
from splatsdb_ui.mixins.settings_mixin import SettingsMixin
from splatsdb_ui.mixins.job_mixin import JobMixin
from splatsdb_ui.mixins.audio_mixin import AudioMixin


class MainWindow(
    FileMixin,
    SearchMixin,
    ViewMixin,
    EditMixin,
    SettingsMixin,
    JobMixin,
    AudioMixin,
    QMainWindow,
):
    """SplatsDB main window — composed from 7 behavior mixins."""

    def __init__(self):
        super().__init__()

        self.signals = SignalBus()
        self.state = AppState()
        self.setWindowTitle("SplatsDB — Vector Search Engine")
        self.setMinimumSize(QSize(1200, 750))
        self.resize(1440, 900)

        self._build_ui()
        self._build_shortcuts()
        self._connect_signals()

        # Initialize mixins
        self.init_settings()
        self.init_audio()

        # Show welcome view on startup
        self.switch_view("welcome")

    def _build_ui(self):
        """Construct the main layout: toolbar | splitter(left+right) | tray."""
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top: Global search bar ──────────────────────────────────
        self.search_bar = GlobalSearchBar()
        root_layout.addWidget(self.search_bar)

        # ── Middle: Main splitter ───────────────────────────────────
        self.main_splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(self.main_splitter, stretch=1)

        # Left: Stacked views
        self.view_stack = QStackedWidget()
        self._register_views()
        self.main_splitter.addWidget(self.view_stack)

        # Right: Parameter panel (collapsible)
        self.param_panel = ParamPanel()
        self.param_panel.setMinimumWidth(280)
        self.param_panel.setMaximumWidth(400)
        self.main_splitter.addWidget(self.param_panel)

        # Splitter proportions: 75% view | 25% params
        self.main_splitter.setSizes([1100, 340])
        self.main_splitter.setCollapsible(1, True)

        # ── Bottom: IO Tray + Job Queue ─────────────────────────────
        self.bottom_splitter = QSplitter(Qt.Vertical)
        root_layout.addWidget(self.bottom_splitter)

        # IO tray (collapsed by default)
        self.io_tray = IOTray()
        self.io_tray.setMaximumHeight(180)
        self.bottom_splitter.addWidget(self.io_tray)

        # Job queue (collapsed by default)
        self.job_panel = JobQueuePanel()
        self.job_panel.setMaximumHeight(150)
        self.bottom_splitter.addWidget(self.job_panel)

        # Bottom splitter defaults
        self.bottom_splitter.setSizes([0, 0])
        self.bottom_splitter.setCollapsible(0, True)
        self.bottom_splitter.setCollapsible(1, True)

        # ── Status bar ──────────────────────────────────────────────
        self.status_bar = SplatsDBStatusBar()
        self.setStatusBar(self.status_bar)

    def _register_views(self):
        """Register all views in the stacked widget."""
        self._views = {}
        view_classes = [
            ("welcome", WelcomeView),
            ("search", SearchView),
            ("collections", CollectionsView),
            ("graph", GraphView),
            ("spatial", SpatialView),
            ("cluster", ClusterView),
            ("benchmark", BenchmarkView),
            ("ocr", OCRView),
        ]
        for name, cls in view_classes:
            view = cls(self.signals, self.state)
            self._views[name] = view
            self.view_stack.addWidget(view)

    def _build_shortcuts(self):
        """Register global keyboard shortcuts."""
        shortcuts = {
            "Ctrl+O": self.file_open,
            "Ctrl+S": self.file_save,
            "Ctrl+F": self.search_bar.focus_search,
            "Ctrl+K": self.search_bar.focus_search,
            "Ctrl+1": lambda: self.switch_view("welcome"),
            "Ctrl+2": lambda: self.switch_view("search"),
            "Ctrl+3": lambda: self.switch_view("collections"),
            "Ctrl+4": lambda: self.switch_view("graph"),
            "Ctrl+5": lambda: self.switch_view("spatial"),
            "Ctrl+6": lambda: self.switch_view("cluster"),
            "Ctrl+7": lambda: self.switch_view("benchmark"),
            "Ctrl+8": lambda: self.switch_view("ocr"),
            "Ctrl+,": self.open_settings,
            "Ctrl+B": self.toggle_bottom_panel,
            "Ctrl+P": self.toggle_param_panel,
            "Escape": self.search_bar.clear_search,
        }
        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)

    def _connect_signals(self):
        """Wire up the global signal bus."""
        self.search_bar.search_requested.connect(
            lambda q: self.signals.search_requested.emit(q)
        )
        self.signals.search_requested.connect(self._on_search)
        self.signals.view_changed.connect(self._on_view_changed)
        self.signals.status_message.connect(self.status_bar.show_message)
        self.signals.job_started.connect(self.job_panel.add_job)
        self.signals.job_finished.connect(self.job_panel.finish_job)
        self.signals.job_progress.connect(self.job_panel.update_job)

    def _on_search(self, query: str):
        """Handle global search — switch to search view and execute."""
        self.switch_view("search")
        search_view = self._views["search"]
        search_view.execute_search(query)

    def _on_view_changed(self, view_name: str):
        """Update param panel when view changes."""
        view = self._views.get(view_name)
        if view and hasattr(view, "get_params"):
            self.param_panel.set_params(view.get_params())

    def switch_view(self, name: str):
        """Switch the stacked widget to the named view."""
        if name in self._views:
            self.view_stack.setCurrentWidget(self._views[name])
            self.signals.view_changed.emit(name)

    def toggle_bottom_panel(self):
        """Toggle the bottom IO tray / job queue."""
        sizes = self.bottom_splitter.sizes()
        if sum(sizes) < 50:
            self.bottom_splitter.setSizes([180, 150])
        else:
            self.bottom_splitter.setSizes([0, 0])

    def toggle_param_panel(self):
        """Toggle the right parameter panel."""
        sizes = self.main_splitter.sizes()
        if sizes[1] < 50:
            self.main_splitter.setSizes([1100, 340])
        else:
            self.main_splitter.setSizes([1440, 0])


class SplatsDBApp(MainWindow):
    """Convenience alias — the full application window."""
    pass
