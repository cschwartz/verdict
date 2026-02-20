from collections.abc import Generator
from typing import Any

from sqlmodel import Session, create_engine

from app.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
)


def get_session() -> Generator[Session, Any, None]:
    """Database session for FastAPI"""
    with Session(engine) as session:
        yield session
