"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings

settings = get_settings()

# Create base class for models
Base = declarative_base()

# Initialize engine and session factory (will be created when needed)
engine = None
SessionLocal = None


def get_engine():
    """Get or create database engine."""
    global engine
    if engine is None:
        engine = create_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    return engine


def get_session_local():
    """Get or create session factory."""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return SessionLocal


def get_db():
    """Dependency to get database session."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()