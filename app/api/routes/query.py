"""
RAG query endpoint.

POST /api/query – retrieve relevant chunks and generate a grounded answer.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_api_key
from app.db.database import get_db
from app.models.schemas import QueryIn, QueryResponse
from app.services.rag import run_rag_pipeline

router = APIRouter(prefix="/api", tags=["Query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question against the knowledge base",
    dependencies=[Depends(verify_api_key)],
)
async def query(
    payload: QueryIn,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """
    Full RAG pipeline in a single request:

    1. The query is embedded with all-MiniLM-L6-v2.
    2. The top-k most similar chunks are retrieved from pgvector (HNSW).
    3. OpenRouter generates a grounded answer from the retrieved context.
    4. The response includes the answer, source chunks, and similarity scores.
    """
    return await run_rag_pipeline(session=db, query_in=payload)
