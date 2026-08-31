import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


def get_database_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://lvbp:lvbp_dev@localhost:5433/luxury_bags",
    )
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Neon's copied URI sometimes includes channel_binding, which psycopg2 rejects.
    url = url.replace("&channel_binding=require", "")
    url = url.replace("?channel_binding=require&", "?")
    url = url.replace("?channel_binding=require", "")
    return url


@lru_cache
def get_engine():
    url = get_database_url()
    connect_args: dict[str, object] = {"sslmode": "require"}
    pool_kwargs: dict[str, object] = {"pool_pre_ping": True}

    # Neon pooler URLs need prepared statements disabled for SQLAlchemy/psycopg2.
    if "-pooler." in url or "neon.tech" in url:
        connect_args["prepare_threshold"] = None
        pool_kwargs["poolclass"] = NullPool

    return create_engine(url, connect_args=connect_args, **pool_kwargs)


def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
