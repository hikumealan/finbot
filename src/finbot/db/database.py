from __future__ import annotations

import hashlib

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from finbot.config import settings
from finbot.models.base import Base
from finbot.security.encryption import get_or_create_key

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _verify_key() -> None:
    """Verify the encryption key exists. The key serves as the access-control
    token for this database; future versions may integrate SQLCipher for
    at-rest encryption on platforms that support it."""
    key = get_or_create_key()
    _marker = settings.data_dir / ".key_hash"
    expected = hashlib.sha256(key.encode()).hexdigest()
    if _marker.exists():
        stored = _marker.read_text().strip()
        if stored != expected:
            raise RuntimeError("Encryption key does not match this database. Restore from backup or reset.")
    else:
        _marker.write_text(expected)


def _get_db_url() -> str:
    return f"sqlite:///{settings.db_path}"


def get_engine():
    global _engine
    if _engine is None:
        settings.ensure_dirs()
        _verify_key()
        _engine = create_engine(
            _get_db_url(),
            echo=False,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def get_session() -> Session:
    return get_session_factory()()


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)


def check_db_health() -> bool:
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
