import os
from dotenv import load_dotenv

load_dotenv()


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        origins = [item.strip() for item in raw.split(",") if item.strip()]
        if origins:
            return origins

    # Backward-compatible fallback behavior for local development.
    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    defaults = [frontend_url] if frontend_url else []
    for value in ("http://localhost:5173", "http://localhost:5174"):
        if value not in defaults:
            defaults.append(value)
    return defaults


class Settings:
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    cors_origins: list[str] = _parse_cors_origins()
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://us.api.openai.com/v1")
    openai_timeout_seconds: int = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
    openai_max_retries: int = int(os.getenv("OPENAI_MAX_RETRIES", "1"))
    openai_embedding_model: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )
    memory_top_k: int = int(os.getenv("MEMORY_TOP_K", "6"))
    google_places_api_key: str | None = os.getenv("GOOGLE_PLACES_API_KEY")
    benchmarking_radius_meters: int = int(os.getenv("BENCHMARKING_RADIUS_METERS", "5000"))
    sentry_dsn: str | None = os.getenv("SENTRY_DSN")
    sentry_environment: str = os.getenv("SENTRY_ENVIRONMENT", "production")

    def validate_openai(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Set it in apps/backend/.env"
            )

    def can_use_openai(self) -> bool:
        if not self.openai_api_key:
            return False
        if os.getenv("PYTEST_CURRENT_TEST"):
            return False
        return True

settings = Settings()
