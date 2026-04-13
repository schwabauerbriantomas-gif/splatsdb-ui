# SplatsDB UI

Professional desktop interface for [SplatsDB](https://github.com/schwabauerbriantomas-gif/splatsdb) — Gaussian Splat vector search engine.

Built with PySide6 (Qt 6), dark theme, mixin architecture.

## Features

- **Multi-model embeddings**: Switch between models at runtime (llama-embed-nemotron-8b, all-MiniLM-L6-v2, BGE, GTE, custom ONNX)
- **OCR integration**: Extract text from images/PDFs → embed → search (Tesseract, PaddleOCR)
- **Vector search**: Semantic search with real-time results, distance visualization
- **Knowledge graph**: Visual graph traversal, entity management, relation mapping
- **Spatial memory**: Wing/Room/Hall navigation with filter panels
- **Cluster dashboard**: Node status, routing, shard management
- **Benchmarks**: GPU/CPU benchmarking with charts
- **Job queue**: Background operations with progress tracking

## Quick Start

```bash
pip install splatsdb-ui

# With all extras (OCR + embeddings):
pip install "splatsdb-ui[all]"

# Launch:
splatsdb-ui
```

### Requirements

- SplatsDB backend running (`splatsdb serve` or MCP mode)
- Python 3.10+
- For CUDA embeddings: NVIDIA GPU + CUDA toolkit

## Architecture

```
splatsdb_ui/
├── main.py              # Entry point
├── app.py               # Application singleton
├── main_window.py       # MainWindow (mixin composition)
├── mixins/              # MainWindow behavior modules
│   ├── file_mixin.py        # File open, drag-drop, recent projects
│   ├── search_mixin.py      # Search bar, results, shortcuts
│   ├── view_mixin.py        # View switching, panels
│   ├── edit_mixin.py        # Clipboard, selection
│   ├── settings_mixin.py    # Preferences, config persistence
│   ├── job_mixin.py         # Job queue, progress
│   └── audio_mixin.py       # UI sounds
├── views/               # Main content views
│   ├── welcome_view.py      # Welcome screen with recent + drop zone
│   ├── search_view.py       # Semantic search
│   ├── collections_view.py  # Collection browser
│   ├── graph_view.py        # Knowledge graph
│   ├── spatial_view.py      # Spatial memory navigator
│   ├── cluster_view.py      # Cluster dashboard
│   ├── benchmark_view.py    # Benchmark runner
│   └── settings_view.py     # Settings panel
├── widgets/             # Reusable UI components
│   ├── vector_viewer.py     # Vector visualization
│   ├── result_card.py       # Search result card
│   ├── status_bar.py        # GPU/VRAM/metrics bar
│   ├── io_tray.py           # Input/output thumbnail tray
│   ├── param_panel.py       # Parameter sidebar
│   ├── job_queue.py         # Background job progress
│   └── search_bar.py        # Global search input
├── workers/             # QThread workers
│   ├── embedding_worker.py  # Embedding generation
│   ├── search_worker.py     # Search queries
│   ├── ocr_worker.py        # OCR text extraction
│   ├── import_worker.py     # Bulk vector import
│   └── benchmark_worker.py  # Benchmark execution
├── embeddings/          # Embedding engine
│   ├── engine.py            # Multi-model embedding engine
│   ├── providers/           # Model providers
│   │   ├── nemotron.py          # llama-embed-nemotron-8b (local CUDA)
│   │   ├── sentence.py          # sentence-transformers
│   │   ├── onnx_provider.py     # ONNX Runtime
│   │   └── remote.py            # Remote API (vLLM, TEI)
│   └── registry.py          # Model registry + discovery
├── dialogs/             # Modal dialogs
│   ├── import_dialog.py     # Import wizard
│   ├── export_dialog.py     # Export options
│   ├── about_dialog.py      # About / credits
│   └── settings_dialog.py   # Full settings
├── utils/               # Utilities
│   ├── api_client.py        # SplatsDB HTTP API client
│   ├── mcp_client.py        # MCP protocol client
│   ├── config.py            # YAML config loader
│   └── signals.py           # Global signal bus
└── resources/
    ├── themes/              # QSS stylesheets
    │   └── dark.qss
    ├── icons/               # SVG icons
    └── sounds/              # UI audio feedback
```

## Configuration

Config file: `~/.splatsdb-ui/config.yaml`

```yaml
backend:
  url: "http://127.0.0.1:8199"
  api_key: ""           # Optional Bearer token

embedding:
  default_model: "llama-embed-nemotron-8b"
  models_dir: "/mnt/d/models"
  device: "cuda"        # cuda | cpu | auto
  
ocr:
  engine: "auto"        # auto | tesseract | paddleocr
  language: "spa+eng"

ui:
  theme: "dark"
  sounds: true
  font_size: 13
```

## License

GPL-3.0 — Same as SplatsDB.
