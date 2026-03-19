from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.models.user import PermissionPublic, Role, RolePublic
from app.queries import get_by_id, get_paginated, get_role_by_name
from app.result import unwrap_optional_or_raise, unwrap_or_raise
from app.schemas.role import RoleDetail, RoleListResponse

router = APIRouter(prefix="/roles", tags=["roles"])


def _to_role_detail(role: Role) -> RoleDetail:
    detail = RoleDetail.model_validate(role, from_attributes=True)
    detail.permissions = [
        PermissionPublic.model_validate(p, from_attributes=True) for p in role.permissions
    ]
    return detail


@router.get("/", response_model=RoleListResponse)
def list_roles(
    session: Session = Depends(get_session),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> RoleListResponse:
    paginated = unwrap_or_raise(
        get_paginated(session, Role, offset, limit, public_class=RolePublic)
    )
    return RoleListResponse(roles=paginated.items, total=paginated.total)


@router.get("/by-name/{name}", response_model=RoleDetail)
def get_role_by_name_route(name: str, session: Session = Depends(get_session)) -> RoleDetail:
    result = get_role_by_name(session, name)
    role = unwrap_optional_or_raise(result, not_found_detail="Role not found")
    return _to_role_detail(role)


@router.get("/{role_id}", response_model=RoleDetail)
def get_role(role_id: int, session: Session = Depends(get_session)) -> RoleDetail:
    result = get_by_id(session, Role, role_id)
    role = unwrap_optional_or_raise(result, not_found_detail="Role not found")
    return _to_role_detail(role)
