"""
RAG service: orchestrates retrieval and generation into a single pipeline call.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.generator import generate_answer
from app.core.retriever import retrieve
from app.models.schemas import QueryIn, QueryResponse

settings = get_settings()


async def run_rag_pipeline(
    session: AsyncSession,
    query_in: QueryIn,
) -> QueryResponse:
    """
    Full RAG pipeline:
      1. Embed the user query.
      2. Retrieve top-k similar chunks from pgvector.
      3. Generate a grounded answer via OpenRouter.
      4. Return structured response with sources.
    """
    chunks = await retrieve(
        session=session,
        query=query_in.query,
        top_k=query_in.top_k,
        metadata_filter=query_in.filter,
    )

    answer = generate_answer(query=query_in.query, chunks=chunks)

    return QueryResponse(
        query=query_in.query,
        answer=answer,
        sources=chunks,
        model=settings.openrouter_model,
        retrieval_top_k=query_in.top_k,
    )
