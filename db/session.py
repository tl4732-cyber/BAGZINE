import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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
    connect_args: dict[str, object] = {}
    # Neon pooler URLs need prepared statements disabled for SQLAlchemy/psycopg2.
    if "-pooler." in url:
        connect_args["prepare_threshold"] = None
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
