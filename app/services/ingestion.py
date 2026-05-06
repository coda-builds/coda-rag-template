"""
Ingestion service: embeds document chunks and inserts them into pgvector.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.embeddings import embed_texts
from app.models.schemas import DocumentIn, DocumentOut

logger = structlog.get_logger(__name__)


async def ingest_documents(
    session: AsyncSession,
    documents: list[DocumentIn],
) -> list[uuid.UUID]:
    """
    Embed and persist a batch of document chunks.

    Returns the list of inserted UUIDs in insertion order.
    """
    if not documents:
        return []

    texts = [doc.content for doc in documents]
    logger.info("Embedding documents", count=len(texts))
    embeddings = embed_texts(texts)

    ids: list[uuid.UUID] = []

    for doc, embedding in zip(documents, embeddings, strict=True):
        vector_literal = f"[{','.join(str(x) for x in embedding)}]"
        result = await session.execute(
            text("""
                INSERT INTO documents (title, content, source, metadata, embedding)
                VALUES (:title, :content, :source, :metadata::jsonb, :embedding::vector)
                RETURNING id
            """),
            {
                "title": doc.title,
                "content": doc.content,
                "source": doc.source,
                "metadata": _serialise_metadata(doc.metadata),
                "embedding": vector_literal,
            },
        )
        row = result.fetchone()
        ids.append(uuid.UUID(str(row.id)))

    # Commit is handled by the get_db dependency in database.py.
    # Do not call session.commit() inside a service — the route dependency
    # owns the transaction boundary and handles rollback on error.
    logger.info("Ingestion complete", inserted=len(ids))
    return ids


async def delete_document(session: AsyncSession, doc_id: uuid.UUID) -> bool:
    """Delete a document by ID. Returns True if a row was deleted."""
    result = await session.execute(
        text("DELETE FROM documents WHERE id = :id RETURNING id"),
        {"id": str(doc_id)},
    )
    return result.fetchone() is not None


async def list_documents(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[DocumentOut]]:
    """Return paginated documents and the total count."""
    total_result = await session.execute(text("SELECT COUNT(*) FROM documents"))
    total = total_result.scalar() or 0

    rows_result = await session.execute(
        text("""
            SELECT id, title, content, source, metadata, created_at
            FROM documents
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {"limit": limit, "offset": offset},
    )
    rows = rows_result.fetchall()

    items = [
        DocumentOut(
            id=uuid.UUID(str(row.id)),
            title=row.title,
            content=row.content,
            source=row.source,
            metadata=row.metadata or {},
            created_at=row.created_at,
        )
        for row in rows
    ]
    return total, items


def _serialise_metadata(metadata: dict[str, Any]) -> str:
    """Convert metadata dict to JSON string for psycopg/asyncpg binding."""
    return json.dumps(metadata)
