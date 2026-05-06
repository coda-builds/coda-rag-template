"""
Embedding service using sentence-transformers all-MiniLM-L6-v2.

The model is loaded once at startup and cached for the lifetime of the process.
all-MiniLM-L6-v2 produces 384-dimensional embeddings and runs well on CPU.
"""

from __future__ import annotations

import structlog
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

_model: SentenceTransformer | None = None


def load_model() -> SentenceTransformer:
    """Load (or return cached) sentence-transformer model."""
    global _model
    if _model is None:
        logger.info("Loading embedding model", model=settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Encode a list of strings into normalised 384-dim vectors.

    Returns a list of float lists suitable for pgvector storage.
    """
    if not texts:
        return []

    model = load_model()
    # normalize_embeddings=True gives unit vectors → cosine similarity
    # is equivalent to dot-product, which pgvector optimises well.
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=32,
    )
    return [v.tolist() for v in vectors]


def embed_query(query: str) -> list[float]:
    """Encode a single query string."""
    return embed_texts([query])[0]
