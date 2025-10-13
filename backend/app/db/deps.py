"""Database dependencies for FastAPI."""

from typing import Generator

from sqlalchemy.orm import Session

from app.db.base import get_session_local


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
