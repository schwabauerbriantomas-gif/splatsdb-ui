# SPDX-License-Identifier: GPL-3.0
"""HTTP API client for SplatsDB backend."""

from __future__ import annotations

import json
from typing import Optional
from dataclasses import dataclass, field

import httpx


@dataclass
class SearchResult:
    """A single search result from SplatsDB."""
    index: int
    score: float
    text: str = ""
    metadata: str = ""
    document_id: str = ""
    category: str = ""


@dataclass
class StoreResult:
    """Result of storing a document."""
    id: str
    status: str


@dataclass
class BackendStatus:
    """Backend server status."""
    n_active: int = 0
    max_splats: int = 0
    dimension: int = 0
    has_hnsw: bool = False
    has_lsh: bool = False
    has_quantization: bool = False
    has_semantic_memory: bool = False


class SplatsDBClient:
    """Async HTTP client for the SplatsDB Axum backend.

    Endpoints:
        POST /store   — Store a memory (text + optional metadata)
        POST /search  — Search memories (query text, top-k)
        POST /status  — Get store stats
        GET  /health  — Health check
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8199", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    def close(self):
        if self._client and not self._client.is_closed:
            self._client.close()

    # ── Health / Status ─────────────────────────────────────────────

    def health(self) -> dict:
        """Check backend health."""
        r = self.client.get("/health")
        r.raise_for_status()
        return r.json()

    def status(self) -> BackendStatus:
        """Get store status."""
        r = self.client.post("/status")
        r.raise_for_status()
        data = r.json()
        return BackendStatus(**data)

    # ── Store ───────────────────────────────────────────────────────

    def store(
        self,
        text: str,
        category: Optional[str] = None,
        doc_id: Optional[str] = None,
        embedding: Optional[list[float]] = None,
    ) -> StoreResult:
        """Store a document in SplatsDB."""
        payload: dict = {"text": text}
        if category:
            payload["category"] = category
        if doc_id:
            payload["id"] = doc_id
        if embedding:
            payload["embedding"] = embedding

        r = self.client.post("/store", json=payload)
        r.raise_for_status()
        data = r.json()
        return StoreResult(id=data["id"], status=data["status"])

    def store_batch(self, documents: list[dict]) -> list[StoreResult]:
        """Store multiple documents."""
        results = []
        for doc in documents:
            results.append(self.store(**doc))
        return results

    # ── Search ──────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 10,
        embedding: Optional[list[float]] = None,
    ) -> list[SearchResult]:
        """Search for similar documents."""
        payload: dict = {"query": query, "top_k": top_k}
        if embedding:
            payload["embedding"] = embedding

        r = self.client.post("/search", json=payload)
        r.raise_for_status()
        data = r.json()
        return [
            SearchResult(
                index=item.get("index", 0),
                score=item.get("score", 0.0),
                metadata=item.get("metadata", ""),
            )
            for item in data.get("results", [])
        ]

    # ── Convenience ─────────────────────────────────────────────────

    def is_connected(self) -> bool:
        """Check if backend is reachable."""
        try:
            self.health()
            return True
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
