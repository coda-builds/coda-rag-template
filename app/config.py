"""
Centralised application configuration.
All values are read from environment variables or the .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    allowed_origins: str = "*"

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str

    # ── OpenRouter ────────────────────────────────────────────────────────────
    openrouter_api_key: str
    openrouter_model: str = "meta-llama/llama-3.1-70b-instruct"

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384  # fixed for all-MiniLM-L6-v2

    # ── RAG ───────────────────────────────────────────────────────────────────
    retrieval_top_k: int = 5
    max_context_tokens: int = 4096

    # ── Optional endpoint auth ────────────────────────────────────────────────
    api_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
