"""
RAG Pipeline Template – FastAPI application entry point.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import documents, query
from app.config import get_settings
from app.core.embeddings import load_model
from app.db.database import check_db_connection
from app.models.schemas import HealthResponse

settings = get_settings()

# ── Structured logging ────────────────────────────────────────────────────────
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(settings.log_level)
    ),
)
logger = structlog.get_logger(__name__)


# ── Lifespan (replaces deprecated @app.on_event) ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Pre-load the embedding model so the first request isn't slow."""
    logger.info("Starting RAG Pipeline API", env=settings.app_env)
    load_model()
    db_ok = await check_db_connection()
    if not db_ok:
        logger.error("Database connection failed on startup – check DATABASE_URL")
    else:
        logger.info("Database connection verified")
    yield
    # Shutdown logic (if needed) goes here


# ── FastAPI application ───────────────────────────────────────────────────────
app = FastAPI(
    title="RAG Pipeline API",
    description=(
        "Production-ready Retrieval-Augmented Generation pipeline. "
        "Ingest documents, then query your knowledge base in natural language."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(documents.router)
app.include_router(query.router)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    """Liveness / readiness probe. Used by Railway's health check."""
    db_ok = await check_db_connection()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database=db_ok,
        embedding_model=settings.embedding_model,
        openrouter_model=settings.openrouter_model,
    )


@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse(
        {"message": "RAG Pipeline API – visit /docs for the interactive API reference."}
    )


# ── Dev entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
