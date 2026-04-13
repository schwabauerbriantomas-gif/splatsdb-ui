#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0
"""Basic import test for splatsdb-ui."""

def test_imports():
    """Verify all modules import correctly."""
    from splatsdb_ui import __version__, __app_name__
    assert __version__ == "0.1.0"
    assert __app_name__ == "SplatsDB"

    from splatsdb_ui.utils.signals import SignalBus
    from splatsdb_ui.utils.state import AppState
    from splatsdb_ui.utils.theme import DARK_QSS
    from splatsdb_ui.utils.api_client import SplatsDBClient, SearchResult, BackendStatus

    from splatsdb_ui.embeddings.engine import (
        EmbeddingEngine, ModelInfo, NemotronProvider,
        SentenceProvider, ONNXProvider, RemoteProvider,
    )
    from splatsdb_ui.embeddings.registry import KNOWN_MODELS, create_engine

    assert "llama-embed-nemotron-8b" in KNOWN_MODELS
    assert KNOWN_MODELS["llama-embed-nemotron-8b"].dimension == 4096

    print("✅ All imports OK")


def test_embedding_engine():
    """Test embedding engine model management."""
    from splatsdb_ui.embeddings.engine import EmbeddingEngine, ModelInfo

    engine = EmbeddingEngine(models_dir="/tmp/test_models")

    info = ModelInfo(
        name="test-model",
        display_name="Test Model",
        dimension=384,
        provider="sentence",
        path="all-MiniLM-L6-v2",
    )
    engine.register_model(info)
    assert len(engine.available_models()) == 1
    assert engine.active_model is None

    engine.unregister_model("test-model")
    assert len(engine.available_models()) == 0

    print("✅ Embedding engine OK")


def test_api_client():
    """Test API client data classes."""
    from splatsdb_ui.utils.api_client import SearchResult, BackendStatus

    r = SearchResult(index=0, score=0.95, metadata="test")
    assert r.score == 0.95

    s = BackendStatus(n_active=1000, dimension=384, has_hnsw=True)
    assert s.n_active == 1000

    print("✅ API client OK")


if __name__ == "__main__":
    test_imports()
    test_embedding_engine()
    test_api_client()
    print("\n🟡 All tests passed!")
