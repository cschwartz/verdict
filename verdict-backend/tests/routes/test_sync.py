from pathlib import Path
from textwrap import dedent

import pytest
from httpx import AsyncClient
from sqlmodel import Session

from app.config import settings
from app.queries import get_role_by_name
from app.result import Ok, Some


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "engineers.yaml").write_text(
        dedent("""\
        name: engineers
        gold_source_id: GRP-001
        permissions:
          - resource: assets
            action: read
    """)
    )
    return tmp_path


async def test_post_sync_returns_200(
    app_client: AsyncClient, db_session, config_dir: Path, monkeypatch
):
    monkeypatch.setattr(settings, "config_basedir", str(config_dir))

    response = await app_client.post("/sync")

    assert response.status_code == 200
    data = response.json()
    assert data["roles_synced"] == 1
    assert data["permissions_synced"] == 1


async def test_post_sync_persists_role(
    app_client: AsyncClient, db_session: Session, config_dir: Path, monkeypatch
):
    monkeypatch.setattr(settings, "config_basedir", str(config_dir))

    await app_client.post("/sync")

    result = get_role_by_name(db_session, "engineers")
    assert isinstance(result, Ok) and isinstance(result.value, Some)


async def test_post_sync_invalid_config_dir_returns_500(
    app_client: AsyncClient, db_session, tmp_path: Path, monkeypatch
):
    monkeypatch.setattr(settings, "config_basedir", str(tmp_path / "nonexistent"))

    response = await app_client.post("/sync")

    assert response.status_code == 500
