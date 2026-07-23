from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── Primary app DB (pooled, port 6543) ────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:123@localhost:5432/devanalytics"

    # ── Direct DB for migrations (port 5432, no pgbouncer) ────────────────────
    # Falls back to DATABASE_URL when not set (local dev without pooler)
    DIRECT_URL: Optional[str] = None

    # ── Legacy key — still accepted so old .env files don't break ─────────────
    SUPABASE_DB_URL: Optional[str] = None

    # ── Other services ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # ── Auth ──────────────────────────────────────────────────────────────────
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── Email (SMTP / nodemailer-style) ───────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""          # matches .env key SMTP_PASS
    SMTP_FROM_NAME: str = "CodeTrack Platform"
    SMTP_FROM_EMAIL: str = ""
    # Set to False to disable email sending (useful in dev/test)
    EMAIL_ENABLED: bool = False

    @property
    def app_db_url(self) -> str:
        """
        URL used by the FastAPI app at runtime.
        Priority: DATABASE_URL > SUPABASE_DB_URL (legacy) > local default
        """
        # If DATABASE_URL still points to localhost but SUPABASE_DB_URL is set,
        # prefer Supabase (backwards-compat for old .env files)
        if "localhost" in self.DATABASE_URL and self.SUPABASE_DB_URL:
            return self.SUPABASE_DB_URL
        return self.DATABASE_URL

    @property
    def migration_db_url(self) -> str:
        """
        URL used by Alembic for migrations — always the direct (non-pooled) connection.
        PgBouncer transaction mode doesn't support DDL / SET statements.
        """
        return self.DIRECT_URL or self.app_db_url

    # Keep old property name so nothing else breaks
    @property
    def active_db_url(self) -> str:
        return self.app_db_url

    class Config:
        env_file = ".env"


settings = Settings()
