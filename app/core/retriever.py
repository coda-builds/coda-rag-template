"""
Vector retriever: queries pgvector with cosine similarity via HNSW index.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

import structlog
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.embeddings import embed_query
from app.models.schemas import RetrievedChunk

logger = structlog.get_logger(__name__)
settings = get_settings()

# Keys in metadata_filter must be safe SQL identifiers.
_SAFE_KEY = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")


async def retrieve(
    session: AsyncSession,
    query: str,
    top_k: int | None = None,
    metadata_filter: dict[str, Any] | None = None,
) -> list[RetrievedChunk]:
    """
    Embed the query and return the top-k most similar document chunks.

    Parameters
    ----------
    session:
        Active async database session.
    query:
        Natural-language query string.
    top_k:
        Number of results to return. Defaults to settings.retrieval_top_k.
    metadata_filter:
        Optional dict of metadata key→value pairs to pre-filter by.
        Example: {"source": "handbook.md"} or {"category": "finance"}.

    Returns
    -------
    List of RetrievedChunk objects ordered by descending similarity.
    """
    k = top_k or settings.retrieval_top_k
    query_vector = embed_query(query)
    vector_literal = f"[{','.join(str(x) for x in query_vector)}]"

    # Build optional metadata WHERE clause.
    # Values are parameterised (safe). Key names are validated against a
    # strict allowlist to prevent SQL injection — an invalid key raises
    # HTTP 422 so the caller gets a meaningful error, not a 500.
    where_clauses = []
    params: dict[str, Any] = {"vector": vector_literal, "k": k}

    if metadata_filter:
        for i, (key, value) in enumerate(metadata_filter.items()):
            if not _SAFE_KEY.match(key):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Metadata filter key {key!r} contains invalid characters. "
                        "Keys must be alphanumeric identifiers (a-z, A-Z, 0-9, _)."
                    ),
                )
            param_name = f"meta_val_{i}"
            where_clauses.append(f"metadata->>'{key}' = :{param_name}")
            params[param_name] = str(value)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = text(f"""
        SELECT
            id,
            title,
            content,
            source,
            metadata,
            1 - (embedding <=> :vector::vector) AS score
        FROM documents
        {where_sql}
        ORDER BY embedding <=> :vector::vector
        LIMIT :k
    """)

    result = await session.execute(sql, params)
    rows = result.fetchall()

    chunks = [
        RetrievedChunk(
            id=uuid.UUID(str(row.id)),
            title=row.title,
            content=row.content,
            source=row.source,
            metadata=row.metadata or {},
            score=float(row.score),
        )
        for row in rows
    ]

    logger.info("Retrieval complete", query=query[:80], returned=len(chunks))
    return chunks
