#!/usr/bin/env python3
"""Take screenshots of the SplatsDB UI using virtual display."""
import sys
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QRect
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QWidget

app = QApplication(sys.argv)

# Apply dark theme
from splatsdb_ui.utils.theme import DARK_QSS
app.setStyleSheet(DARK_QSS)

from splatsdb_ui.app import MainWindow

window = MainWindow()
window.resize(1440, 900)
window.show()

# Screenshot 1: Full window with engine switcher + welcome view
def screenshot1():
    pixmap = window.grab()
    pixmap.save("/tmp/splatsdb_ui_welcome.png", "png")
    print(f"Screenshot 1: {pixmap.width()}x{pixmap.height()}")
    
    # Screenshot 2: Switch to search view
    window.switch_view("search")
    QTimer.singleShot(100, screenshot2)

def screenshot2():
    pixmap = window.grab()
    pixmap.save("/tmp/splatsdb_ui_search.png", "png")
    print(f"Screenshot 2: {pixmap.width()}x{pixmap.height()}")
    
    # Screenshot 3: Config editor
    window.switch_view("config")
    QTimer.singleShot(100, screenshot3)

def screenshot3():
    pixmap = window.grab()
    pixmap.save("/tmp/splatsdb_ui_config.png", "png")
    print(f"Screenshot 3: {pixmap.width()}x{pixmap.height()}")
    
    # Screenshot 4: Graph view
    window.switch_view("graph")
    QTimer.singleShot(100, screenshot4)

def screenshot4():
    pixmap = window.grab()
    pixmap.save("/tmp/splatsdb_ui_graph.png", "png")
    print(f"Screenshot 4: {pixmap.width()}x{pixmap.height()}")
    
    # Screenshot 5: Collections view
    window.switch_view("collections")
    QTimer.singleShot(100, screenshot5)

def screenshot5():
    pixmap = window.grab()
    pixmap.save("/tmp/splatsdb_ui_collections.png", "png")
    print(f"Screenshot 5: {pixmap.width()}x{pixmap.height()}")
    
    # Screenshot 6: Spatial view
    window.switch_view("spatial")
    QTimer.singleShot(100, screenshot6)

def screenshot6():
    pixmap = window.grab()
    pixmap.save("/tmp/splatsdb_ui_spatial.png", "png")
    print(f"Screenshot 6: {pixmap.width()}x{pixmap.height()}")
    
    # Screenshot 7: Cluster view
    window.switch_view("cluster")
    QTimer.singleShot(100, screenshot7)

def screenshot7():
    pixmap = window.grab()
    pixmap.save("/tmp/splatsdb_ui_cluster.png", "png")
    print(f"Screenshot 7: {pixmap.width()}x{pixmap.height()}")
    
    # Screenshot 8: Benchmark view
    window.switch_view("benchmark")
    QTimer.singleShot(100, screenshot8)

def screenshot8():
    pixmap = window.grab()
    pixmap.save("/tmp/splatsdb_ui_benchmark.png", "png")
    print(f"Screenshot 8: {pixmap.width()}x{pixmap.height()}")
    
    # Screenshot 9: OCR view
    window.switch_view("ocr")
    QTimer.singleShot(100, screenshot9)

def screenshot9():
    pixmap = window.grab()
    pixmap.save("/tmp/splatsdb_ui_ocr.png", "png")
    print(f"Screenshot 9: {pixmap.width()}x{pixmap.height()}")
    
    app.quit()

QTimer.singleShot(500, screenshot1)
app.exec()
print("All screenshots taken!")
