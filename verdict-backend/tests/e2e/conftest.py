"""Fixtures for E2E tests that run against real services."""

import os
from collections.abc import Generator

import httpx
import pytest
import sqlalchemy as sa

from app.db import engine
from app.models.asset import Asset
from app.models.system import System, asset_system


@pytest.fixture(scope="session", autouse=True)
def _clean_db() -> Generator[None, None, None]:
    """Truncate all tables before and after the e2e session."""
    _truncate()
    yield
    _truncate()


def _truncate() -> None:
    with engine.begin() as conn:
        conn.execute(sa.delete(asset_system))
        conn.execute(sa.delete(System))
        conn.execute(sa.delete(Asset))


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ.get("VERDICT_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def http_client(base_url: str) -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        yield client
