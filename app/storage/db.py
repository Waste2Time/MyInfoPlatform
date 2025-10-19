from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os
from typing import Iterator
from contextlib import contextmanager

# Read configuration from environment. If DATABASE_URL is not set we fall back to a local sqlite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
ECHO = os.getenv("SQL_ECHO", "False").lower() in ("1", "true", "yes")

# Create engine and session factory
# pool_pre_ping helps with stale connections when using long-lived processes
engine = create_engine(DATABASE_URL, echo=ECHO, future=True, pool_pre_ping=True)

# Use SQLAlchemy Session class for typing clarity
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)

# Declarative base for ORM models
Base = declarative_base()


@contextmanager
def get_session() -> Iterator[Session]:
    """Context manager that yields a SQLAlchemy Session and handles commit/rollback.

    Usage:
        with get_session() as session:
            session.add(obj)
            # commit happens automatically on successful exit
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables registered on Base.

    This function imports the models module (which typically imports Base) so that
    model classes are registered before creating tables. It avoids circular import
    problems by importing inside the function.
    """
    # Import models to ensure they are registered with Base.metadata
    try:
        # Prefer absolute import in package layout
        import importlib
        importlib.import_module("app.storage.models")
    except Exception:
        # Fallback to relative import
        try:
            from . import models  # type: ignore
        except Exception:
            # If importing models fails, raise a clear error
            raise

    Base.metadata.create_all(bind=engine)


def test_connection() -> bool:
    """Quick smoke-test for DB connectivity. Returns True on success, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
