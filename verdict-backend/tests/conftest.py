from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.db import engine, get_session
from app.main import app
from tests.factories import BaseModelFactory


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    BaseModelFactory.set_session(session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
async def app_client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client with the DB dependency overridden."""

    def _override_get_session() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
