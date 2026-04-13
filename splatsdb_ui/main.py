# SPDX-License-Identifier: GPL-3.0
"""Application entry point."""

import sys
import os


def run():
    """Launch the SplatsDB UI application."""
    # High DPI support
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon

    from splatsdb_ui import __app_name__
    from splatsdb_ui.app import SplatsDBApp

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setOrganizationName("SplatsDB")
    app.setApplicationVersion("0.1.0")

    # Load dark theme
    from splatsdb_ui.utils.theme import load_theme
    load_theme(app)

    window = SplatsDBApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
