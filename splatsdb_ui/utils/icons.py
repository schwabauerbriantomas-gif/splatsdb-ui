# SPDX-License-Identifier: GPL-3.0
"""Icon system — clean geometric Unicode symbols. No emojis.

Consistent visual language across the entire UI:
  - Navigation: filled geometric shapes
  - Actions: arrows, plus, minus, check
  - Status: dots, circles
  - Indicators: squares, diamonds, triangles
"""

# Navigation / View icons (used in tabs, sidebar, menus)
HOME       = "\u25C6"   # ◆ Diamond
SEARCH     = "\u25B8"   # ▸ Right triangle
COLLECTION = "\u25A0"   # ■ Square
GRAPH      = "\u25C7"   # ◇ Diamond outline
SPATIAL    = "\u25CB"   # ○ Circle outline
CLUSTER    = "\u25BD"   # ▽ Down triangle
BENCHMARK  = "\u25B2"   # ▲ Up triangle
OCR        = "\u25A1"   # □ Square outline
CONFIG     = "\u2699"   # ⚙ Gear

# Status indicators
DOT_ON     = "\u25CF"   # ● Filled circle
DOT_OFF    = "\u25CB"   # ○ Open circle
DOT_WARN   = "\u25D0"   # ◐ Half circle
DOT_ERR    = "\u25D1"   # ◑ Half circle (reverse)

# Actions
PLAY       = "\u25B6"   # ▶ Play
STOP       = "\u25A0"   # ■ Stop (square)
PAUSE      = "\u2590"   # ▐ Pause bar
REFRESH    = "\u21BB"   # ↻ Refresh
ADD        = "\u002B"   # + Plus
REMOVE     = "\u2212"   # − Minus
CHECK      = "\u2713"   # ✓ Check
CROSS      = "\u2717"   # ✗ Cross
ARROW_R    = "\u2192"   # → Right arrow
ARROW_D    = "\u2193"   # ↓ Down arrow
ARROW_U    = "\u2191"   # ↑ Up arrow

# Content types
FILE       = "\u25A3"   # ▣ Square with fill
FOLDER     = "\u25A4"   # ▤ Square with lines
LINK       = "\u2194"   # ↔ Left-right arrow
IMAGE      = "\u25A8"   # ▨ Square with dots
TEXT       = "\u25A9"   # ▩ Square with crosshatch

# Misc
GEAR       = "\u2699"   # ⚙ Gear
PIN        = "\u25C8"   # ◈ Diamond with dot
BULLET     = "\u2022"   # • Bullet
PIPE       = "\u2502"   # │ Vertical bar
SEPARATOR  = "\u2500"   # ─ Horizontal bar

# Tab labels (icon + text)
def tab_label(view_id: str) -> str:
    labels = {
        "welcome":     f"{HOME} Home",
        "search":      f"{SEARCH} Search",
        "collections": f"{COLLECTION} Collections",
        "graph":       f"{GRAPH} Graph",
        "spatial":     f"{SPATIAL} Spatial",
        "cluster":     f"{CLUSTER} Cluster",
        "benchmark":   f"{BENCHMARK} Benchmark",
        "ocr":         f"{OCR} OCR",
        "config":      f"{GEAR} Config",
    }
    return labels.get(view_id, view_id.title())
