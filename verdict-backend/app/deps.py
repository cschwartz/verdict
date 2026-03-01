from collections.abc import Generator

import httpx


def get_http_client() -> Generator[httpx.Client, None, None]:
    with httpx.Client() as client:
        yield client
