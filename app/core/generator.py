"""
Answer generator: calls OpenRouter API with retrieved context to produce
a grounded, cited response.

OpenRouter exposes an OpenAI-compatible interface, so the standard openai
package is used with a custom base_url.
"""

from __future__ import annotations

import structlog
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models.schemas import RetrievedChunk

logger = structlog.get_logger(__name__)
settings = get_settings()

_client: OpenAI | None = None


def get_openrouter_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _client


SYSTEM_PROMPT = """\
You are a helpful assistant that answers questions using only the provided context excerpts.

Rules:
- Base your answer solely on the context below. Do not use prior knowledge.
- If the context does not contain enough information to answer, say so clearly.
- Be concise and precise. Use plain language.
- When referencing specific information, mention which document or section it came from.
- Do not fabricate facts, statistics, or details not present in the context.
"""


def _build_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into a readable context block."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        source_label = f" [{chunk.source}]" if chunk.source else ""
        parts.append(
            f"--- Excerpt {i}{source_label} ---\n"
            f"Title: {chunk.title}\n\n"
            f"{chunk.content}\n"
        )
    return "\n".join(parts)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def generate_answer(query: str, chunks: list[RetrievedChunk]) -> str:
    """
    Send the query + context to OpenRouter and return the generated answer.

    Retries up to 3 times with exponential backoff on transient errors.
    """
    if not chunks:
        return (
            "I could not find any relevant information in the knowledge base "
            "to answer your question. Please try rephrasing, or check that the "
            "relevant documents have been ingested."
        )

    context = _build_context(chunks)
    user_message = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"

    client = get_openrouter_client()
    response = client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,  # low temperature for factual, grounded answers
        max_tokens=1024,
    )

    answer = response.choices[0].message.content.strip()
    tokens = response.usage.total_tokens if response.usage else "n/a"
    logger.info("Generation complete", model=settings.openrouter_model, tokens=tokens)
    return answer
