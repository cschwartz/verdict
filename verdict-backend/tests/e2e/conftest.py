"""Fixtures for E2E tests that run against real services."""

from collections.abc import Generator

import httpx
import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def http_client(base_url: str) -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        yield client
