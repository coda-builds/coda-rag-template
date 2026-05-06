"""
Pydantic schemas for API request and response bodies.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Document ingestion ─────────────────────────────────────────────────────────


class DocumentIn(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=500, description="Document title or heading"
    )
    content: str = Field(
        ..., min_length=1, description="Raw text content of this chunk"
    )
    source: str | None = Field(
        None, max_length=500, description="Origin identifier (filename, URL, etc.)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary key-value metadata"
    )


class BatchDocumentsIn(BaseModel):
    documents: list[DocumentIn] = Field(..., min_length=1, max_length=500)


class DocumentOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    source: str | None
    metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    total: int
    items: list[DocumentOut]


class IngestResponse(BaseModel):
    inserted: int
    ids: list[uuid.UUID]


# ── Query / RAG ────────────────────────────────────────────────────────────────


class QueryIn(BaseModel):
    query: str = Field(
        ..., min_length=1, max_length=2000, description="Natural-language question"
    )
    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve")
    filter: dict[str, Any] | None = Field(
        None,
        description='Optional metadata filter, e.g. {"source": "handbook.md"}',
    )

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()


class RetrievedChunk(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    source: str | None
    metadata: dict[str, Any]
    score: float = Field(
        ..., description="Cosine similarity score (0–1, higher = more relevant)"
    )


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[RetrievedChunk]
    model: str
    retrieval_top_k: int


# ── Health ─────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    database: bool
    embedding_model: str
    openrouter_model: str
    version: str = "1.0.0"
