from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from shared.config import settings


def _is_supabase(url: str) -> bool:
    return "supabase.com" in url or "supabase.co" in url


def _is_pooler(url: str) -> bool:
    """PgBouncer transaction-mode pooler runs on port 6543."""
    return ":6543" in url or "pgbouncer=true" in url


def _build_engine(url: str):
    connect_args = {}
    engine_kwargs = {
        "pool_pre_ping": True,
    }

    if _is_supabase(url):
        # SSL is required for all Supabase connections
        connect_args["sslmode"] = "require"

    if _is_pooler(url):
        # PgBouncer transaction mode:
        #   - No server-side prepared statements
        #   - Smaller pool (pooler manages its own)
        #   - No pool_size / max_overflow (use NullPool or small fixed pool)
        connect_args["options"] = "-c statement_timeout=30000"
        engine_kwargs.update({
            "pool_size": 5,
            "max_overflow": 10,
            "pool_recycle": 300,
            # Disable SQLAlchemy's use of SAVEPOINT inside transactions
            # (pgbouncer transaction mode doesn't support it)
        })
    else:
        # Direct connection — full pool
        engine_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 600,
        })

    engine_kwargs["connect_args"] = connect_args

    # Strip pgbouncer=true query param — psycopg2 doesn't understand it
    clean_url = url.split("?")[0] if "pgbouncer=true" in url else url

    return create_engine(clean_url, **engine_kwargs)


engine = _build_engine(settings.app_db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
