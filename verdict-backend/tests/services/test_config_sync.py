from pathlib import Path
from textwrap import dedent

from sqlmodel import Session, select

from app.errors import ConfigError, ValidationError
from app.models.gold_source import GoldSourceType
from app.models.user import Permission, Role
from app.result import Err, Ok
from app.schemas.config import PermissionConfig, RoleConfig
from app.services.config_sync import (
    _upsert_permission,
    _upsert_role,
    load_role_configs,
    sync_config,
)

# --- load_role_configs ---


def test_load_role_configs_returns_roles(tmp_path):
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

    result = load_role_configs(tmp_path)

    assert isinstance(result, Ok)
    assert len(result.value) == 1
    assert result.value[0].name == "engineers"
    assert result.value[0].gold_source_id == "GRP-001"
    assert len(result.value[0].permissions) == 1


def test_load_role_configs_invalid_yaml_returns_config_error(tmp_path):
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "bad.yaml").write_text("name: [unclosed bracket\n")

    result = load_role_configs(tmp_path)

    assert isinstance(result, Err)
    assert isinstance(result.value, ConfigError)


def test_load_role_configs_invalid_schema_returns_validation_error(tmp_path):
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "bad.yaml").write_text(
        dedent("""\
        name: engineers
        # missing gold_source_id and permissions
    """)
    )

    result = load_role_configs(tmp_path)

    assert isinstance(result, Err)
    assert isinstance(result.value, ValidationError)


def test_load_role_configs_empty_dir_returns_empty_list(tmp_path):
    (tmp_path / "roles").mkdir()

    result = load_role_configs(tmp_path)

    assert isinstance(result, Ok)
    assert result.value == []


# --- _upsert_permission ---


def test_upsert_permission_creates_new(db_session: Session):
    cfg = PermissionConfig(resource="assets", action="read")

    result = _upsert_permission(db_session, cfg)

    assert isinstance(result, Ok)
    assert result.value.resource == "assets"
    assert result.value.action == "read"
    assert result.value.id is not None


def test_upsert_permission_returns_existing(db_session: Session):
    cfg = PermissionConfig(resource="assets", action="read")
    first = _upsert_permission(db_session, cfg)
    assert isinstance(first, Ok)

    second = _upsert_permission(db_session, cfg)

    assert isinstance(second, Ok)
    assert second.value.id == first.value.id


# --- _upsert_role ---


def test_upsert_role_creates_new(db_session: Session):
    cfg = RoleConfig(name="engineers", gold_source_id="GRP-001", permissions=[])

    result = _upsert_role(db_session, cfg)

    assert isinstance(result, Ok)
    assert result.value.name == "engineers"
    assert result.value.gold_source_id == "GRP-001"
    assert result.value.gold_source_type == GoldSourceType.IAM_GROUP


def test_upsert_role_updates_existing_name(db_session: Session):
    cfg = RoleConfig(name="engineers", gold_source_id="GRP-001", permissions=[])
    first = _upsert_role(db_session, cfg)
    assert isinstance(first, Ok)

    updated_cfg = RoleConfig(name="senior-engineers", gold_source_id="GRP-001", permissions=[])
    result = _upsert_role(db_session, updated_cfg)

    assert isinstance(result, Ok)
    assert result.value.name == "senior-engineers"
    roles = db_session.exec(select(Role).where(Role.gold_source_id == "GRP-001")).all()
    assert len(roles) == 1


# --- sync_config ---


def test_sync_config_upserts_roles_and_permissions(db_session: Session, tmp_path: Path):
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "engineers.yaml").write_text(
        dedent("""\
        name: engineers
        gold_source_id: GRP-001
        permissions:
          - resource: assets
            action: read
          - resource: systems
            action: read
    """)
    )

    result = sync_config(db_session, tmp_path)

    assert isinstance(result, Ok)
    assert result.value.roles_synced == 1
    assert result.value.permissions_synced == 2

    roles = db_session.exec(select(Role)).all()
    assert len(roles) == 1
    assert roles[0].name == "engineers"

    permissions = db_session.exec(select(Permission)).all()
    assert len(permissions) == 2


def test_sync_config_idempotent(db_session: Session, tmp_path: Path):
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

    first = sync_config(db_session, tmp_path)
    assert isinstance(first, Ok)
    result = sync_config(db_session, tmp_path)

    assert isinstance(result, Ok)
    assert result.value.roles_synced == 1
    assert result.value.permissions_synced == 1

    roles = db_session.exec(select(Role)).all()
    assert len(roles) == 1
    permissions = db_session.exec(select(Permission)).all()
    assert len(permissions) == 1
