import logging
from pathlib import Path

import yaml
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, select

from app.errors import ConfigError, ConfigSyncError, DBError, ValidationError, db_error_from
from app.models.gold_source import GoldSourceType
from app.models.user import Permission, PermissionPublic, Role, RolePermission, RolePublic
from app.queries import sync_join_table, upsert_by_gold_source
from app.result import Err, Ok, Result
from app.schemas.config import PermissionConfig, RoleConfig
from app.schemas.sync import SyncResponse

logger = logging.getLogger(__name__)


def load_role_configs(basedir: Path) -> Result[list[RoleConfig], ConfigSyncError]:
    roles_dir = basedir / "roles"
    if not roles_dir.is_dir():
        return Err(ConfigError(path=str(roles_dir), raw="roles directory not found"))
    configs: list[RoleConfig] = []
    for path in sorted(roles_dir.glob("*.yaml")):
        try:
            raw = path.read_text()
            data = yaml.safe_load(raw)
        except Exception as e:
            return Err(ConfigError(path=str(path), raw=str(e)))
        if data is None:
            return Err(ConfigError(path=str(path), raw="empty yaml file"))
        try:
            configs.append(RoleConfig.model_validate(data))
        except PydanticValidationError as e:
            return Err(ValidationError(raw=str(e)))
    return Ok(configs)


def _upsert_permission(
    session: Session,
    cfg: PermissionConfig,
) -> Result[PermissionPublic, DBError]:
    stmt = select(Permission).where(
        Permission.resource == cfg.resource,
        Permission.subresource == cfg.subresource,
        Permission.action == cfg.action,
    )
    try:
        existing = session.exec(stmt).first()
    except OperationalError as e:
        return Err(db_error_from(e))

    if existing is not None:
        return Ok(PermissionPublic.model_validate(existing, from_attributes=True))

    new = Permission(
        resource=cfg.resource,
        subresource=cfg.subresource,
        action=cfg.action,
    )
    session.add(new)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        try:
            existing = session.exec(stmt).first()
        except OperationalError as e:
            return Err(db_error_from(e))
        if existing is not None:
            return Ok(PermissionPublic.model_validate(existing, from_attributes=True))
        return Err(
            DBError(
                statement=None, raw="concurrent insert race: permission not found after rollback"
            )
        )
    except OperationalError as e:
        return Err(db_error_from(e))
    return Ok(PermissionPublic.model_validate(new, from_attributes=True))


def _upsert_role(
    session: Session,
    cfg: RoleConfig,
) -> Result[RolePublic, DBError]:
    def on_existing(existing: Role) -> None:
        existing.name = cfg.name

    def make_new() -> Role:
        return Role(
            name=cfg.name,
            gold_source_type=GoldSourceType.IAM_GROUP,
            gold_source_id=cfg.gold_source_id,
        )

    return upsert_by_gold_source(
        session,
        Role,
        GoldSourceType.IAM_GROUP,
        cfg.gold_source_id,
        public_class=RolePublic,
        on_existing=on_existing,
        make_new=make_new,
    )


def _sync_role_permissions(
    session: Session,
    role_id: int,
    permission_ids: list[int],
) -> Result[int, DBError]:
    t = RolePermission.__table__  # type: ignore[attr-defined]  # SQLModel does not expose __table__ in stubs but it exists on table=True models
    result = sync_join_table(session, t.c.role_id, role_id, t.c.permission_id, permission_ids)
    if isinstance(result, Err):
        return Err(result.value)
    return Ok(len(permission_ids))


def sync_config(
    session: Session,
    basedir: Path,
) -> Result[SyncResponse, ConfigSyncError]:
    configs_result = load_role_configs(basedir)
    if isinstance(configs_result, Err):
        return Err(configs_result.value)

    total_permissions = 0
    for cfg in configs_result.value:
        role_result = _upsert_role(session, cfg)
        if isinstance(role_result, Err):
            return Err(role_result.value)
        role = role_result.value

        permission_ids: list[int] = []
        for perm_cfg in cfg.permissions:
            perm_result = _upsert_permission(session, perm_cfg)
            if isinstance(perm_result, Err):
                return Err(perm_result.value)
            permission_ids.append(perm_result.value.id)

        sync_result = _sync_role_permissions(session, role.id, permission_ids)
        if isinstance(sync_result, Err):
            return Err(sync_result.value)
        total_permissions += sync_result.value

    return Ok(
        SyncResponse(
            roles_synced=len(configs_result.value),
            permissions_synced=total_permissions,
        )
    )
