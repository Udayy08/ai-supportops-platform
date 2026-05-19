"""
AI SupportOps Backend
=====================
FastAPI application configuration and settings management.
Uses pydantic-settings for typed, validated environment variable loading.

Key design decision for list fields (CORS origins, allowed hosts):
  pydantic-settings v2 treats `list[...]` fields as "complex" and calls
  json.loads() on the raw env string before any field_validator can run.
  A bare URL like `http://localhost:3000` is not JSON → crashes.

  Solution: declare them as plain `str` fields (never JSON-decoded),
  then expose the parsed list via `@property`. The env var name is
  preserved by using `validation_alias`.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central settings class — reads from environment variables / .env file.
    All fields are typed and validated by Pydantic v2.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "AI SupportOps"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)

    # ── API ──────────────────────────────────────────────────────────────────
    api_v1_prefix: str = "/api/v1"

    # Stored as plain `str` so pydantic-settings never tries JSON-decoding.
    # Use comma-separated values in .env — no quotes, no brackets:
    #   BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    #   ALLOWED_HOSTS=localhost,127.0.0.1
    # Access the parsed list via the @property wrappers below.
    cors_origins_raw: str = Field(default="", alias="backend_cors_origins")
    allowed_hosts_raw: str = Field(default="localhost,127.0.0.1", alias="allowed_hosts")

    # ── JWT ──────────────────────────────────────────────────────────────────
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── PostgreSQL ───────────────────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "supportops"
    postgres_user: str = "supportops"
    postgres_password: str = Field(..., min_length=1)

    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> str:
        """Async PostgreSQL DSN assembled from individual fields."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def sync_database_url(self) -> str:
        """Sync DSN for Alembic migrations."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_name: str = "supportops_kb"

    @computed_field  # type: ignore[misc]
    @property
    def chroma_url(self) -> str:
        return f"http://{self.chroma_host}:{self.chroma_port}"

    # ── LLM / OpenAI ─────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o"
    openai_fast_model: str = "gpt-4o-mini"

    # ── LangSmith ────────────────────────────────────────────────────────────
    langchain_tracing_v2: bool = False
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: str = ""
    langchain_project: str = "ai-supportops"

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    rate_limit_per_minute: int = 100

    # ── Sentry ───────────────────────────────────────────────────────────────
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.1

    # ── Email ────────────────────────────────────────────────────────────────
    sendgrid_api_key: str = ""
    notification_from_email: str = "noreply@supportops.ai"

    # ── Pagination ────────────────────────────────────────────────────────────
    default_page_size: int = 20
    max_page_size: int = 100

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_csv(value: str) -> list[str]:
        """Split a comma-separated string into a cleaned list, ignoring blanks."""
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def backend_cors_origins(self) -> list[str]:
        """Parsed list of allowed CORS origins."""
        return self._parse_csv(self.cors_origins_raw)

    @property
    def allowed_hosts(self) -> list[str]:
        """Parsed list of trusted Host header values."""
        hosts = self._parse_csv(self.allowed_hosts_raw)
        return hosts if hosts else ["localhost", "127.0.0.1"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Use as a FastAPI dependency: `settings: Settings = Depends(get_settings)`.
    """
    return Settings()  # type: ignore[call-arg]


# Module-level singleton for use outside of FastAPI DI context
settings: Settings = get_settings()
