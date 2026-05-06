"""
Document management endpoints.

POST   /api/documents          – ingest a single document chunk
POST   /api/documents/batch    – ingest up to 500 chunks in one request
GET    /api/documents          – list all documents (paginated)
DELETE /api/documents/{id}     – remove a document by ID
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_api_key
from app.db.database import get_db
from app.models.schemas import (
    BatchDocumentsIn,
    DocumentIn,
    DocumentList,
    IngestResponse,
)
from app.services.ingestion import (
    delete_document,
    ingest_documents,
    list_documents,
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a single document chunk",
    dependencies=[Depends(verify_api_key)],
)
async def ingest_one(
    document: DocumentIn,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    ids = await ingest_documents(db, [document])
    return IngestResponse(inserted=1, ids=ids)


@router.post(
    "/batch",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a batch of document chunks (max 500)",
    dependencies=[Depends(verify_api_key)],
)
async def ingest_batch(
    payload: BatchDocumentsIn,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    ids = await ingest_documents(db, payload.documents)
    return IngestResponse(inserted=len(ids), ids=ids)


@router.get(
    "",
    response_model=DocumentList,
    summary="List ingested documents",
    dependencies=[Depends(verify_api_key)],
)
async def get_documents(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> DocumentList:
    total, items = await list_documents(db, limit=limit, offset=offset)
    return DocumentList(total=total, items=items)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document by ID",
    dependencies=[Depends(verify_api_key)],
)
async def remove_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_document(db, document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
