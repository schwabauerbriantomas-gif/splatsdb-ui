# SPDX-License-Identifier: GPL-3.0
"""Global signal bus — decoupled communication between components."""

from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    """Central signal hub. All components communicate through this bus
    to avoid tight coupling between views, workers, and the main window."""

    # ── Navigation ──────────────────────────────────────────────────
    view_changed = Signal(str)              # view name
    search_requested = Signal(str)          # query text

    # ── Data operations ─────────────────────────────────────────────
    vectors_imported = Signal(str, int)     # collection_name, count
    search_results = Signal(list)           # list of SearchResult
    document_stored = Signal(str)           # doc_id
    document_deleted = Signal(str)          # doc_id

    # ── Embedding engine ────────────────────────────────────────────
    model_loaded = Signal(str)              # model_name
    model_loading = Signal(str, int)        # model_name, progress %
    embedding_generated = Signal(int)       # count

    # ── OCR ─────────────────────────────────────────────────────────
    ocr_completed = Signal(str, str)        # file_path, extracted_text
    ocr_error = Signal(str, str)            # file_path, error_msg

    # ── Job queue ───────────────────────────────────────────────────
    job_started = Signal(str, str)          # job_id, description
    job_finished = Signal(str, bool)        # job_id, success
    job_progress = Signal(str, int)         # job_id, progress %

    # ── Cluster ─────────────────────────────────────────────────────
    node_joined = Signal(str)               # node_id
    node_left = Signal(str)                 # node_id
    cluster_status = Signal(dict)           # status dict

    # ── Status ──────────────────────────────────────────────────────
    status_message = Signal(str)            # status bar message
    gpu_info = Signal(dict)                 # GPU stats
    vram_usage = Signal(float, float)       # used_gb, total_gb
