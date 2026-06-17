from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.models.base import Base

_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _pool_options(database_url: str) -> dict:
    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        return {"poolclass": StaticPool}
    if database_url.startswith("sqlite"):
        return {}
    return {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
    }


def configure_database(database_url: str | None = None) -> Engine:
    """Configure the process-wide SQLAlchemy engine.

    Tests call this with a temporary SQLite URL. Docker/prod uses DATABASE_URL.
    """
    global _engine, SessionLocal
    url = database_url or get_settings().DATABASE_URL
    _engine = create_engine(
        url,
        future=True,
        connect_args=_connect_args(url),
        **_pool_options(url),
    )
    SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False, expire_on_commit=False, future=True)
    return _engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        return configure_database()
    return _engine


def create_schema() -> None:
    # Ensure all models are imported before creating tables.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def drop_schema() -> None:
    import app.models  # noqa: F401

    Base.metadata.drop_all(bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    global SessionLocal
    if SessionLocal is None:
        configure_database()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    global SessionLocal
    if SessionLocal is None:
        configure_database()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def ping_database() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
