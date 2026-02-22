from httpx import AsyncClient
from sqlalchemy import text
from sqlmodel import Session


async def test_root_returns_200(app_client: AsyncClient) -> None:
    """Verify the app_client fixture can hit the root endpoint."""
    response = await app_client.get("/")
    assert response.status_code == 200


def test_db_session_executes_query(db_session: Session) -> None:
    """Verify the db_session fixture connects to verdict_test."""
    result = db_session.exec(text("SELECT 1")).scalar()
    assert result == 1
