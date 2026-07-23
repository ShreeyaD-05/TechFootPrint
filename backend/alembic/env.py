from logging.config import fileConfig
from sqlalchemy import pool, create_engine
from alembic import context
from shared.database import Base
from shared.models import *  # noqa: F401,F403  — registers all models with metadata
from shared.config import settings
import os

config = context.config

# ── Resolve migration URL ──────────────────────────────────────────────────────
# Priority:
#   1. DATABASE_URL env var set explicitly by a migration script (e.g. migrate_to_supabase.py)
#   2. DIRECT_URL from .env  (port 5432, no pgbouncer — required for DDL)
#   3. active_db_url fallback
_env_override = os.environ.get("DATABASE_URL")
if _env_override and "localhost" not in _env_override:
    # An explicit non-local override was passed in — use it as-is
    migration_url = _env_override
else:
    migration_url = settings.migration_db_url

# Strip pgbouncer query param if somehow present (DDL must not go through pooler)
migration_url = migration_url.split("?")[0]

# NOTE: We do NOT call config.set_main_option() because configparser chokes on
# percent-encoded characters (e.g. %40 in passwords).  We pass the URL directly
# to create_engine() instead.

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _make_engine(url: str):
    connect_args = {}
    if "supabase" in url:
        connect_args["sslmode"] = "require"
    return create_engine(url, poolclass=pool.NullPool, connect_args=connect_args)


def run_migrations_offline() -> None:
    context.configure(
        url=migration_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = _make_engine(migration_url)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Compare server defaults so Alembic detects column changes properly
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
