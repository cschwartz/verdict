import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import Permission, RolePermission, UserRole
from tests.factories.user import PermissionFactory, RoleFactory, UserFactory


def test_user_persists(db_session):
    user = UserFactory.create()
    db_session.refresh(user)

    assert user.id is not None


def test_role_persists(db_session):
    role = RoleFactory.create()
    db_session.refresh(role)

    assert role.id is not None


def test_permission_persists(db_session):
    perm = PermissionFactory.create()
    db_session.refresh(perm)

    assert perm.id is not None


def test_user_has_role(db_session):
    user = UserFactory.create()
    role = RoleFactory.create()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.flush()
    db_session.refresh(user)

    assert role in user.roles


def test_role_has_permission(db_session):
    role = RoleFactory.create()
    perm = PermissionFactory.create()
    db_session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db_session.flush()
    db_session.refresh(role)

    assert perm in role.permissions


def test_user_permissions_traversal(db_session):
    user = UserFactory.create()
    role = RoleFactory.create()
    perm = PermissionFactory.create()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db_session.flush()
    db_session.refresh(user)

    all_permissions = [p for r in user.roles for p in r.permissions]

    assert perm in all_permissions


def test_duplicate_permission_raises_integrity_error(db_session):
    db_session.add(Permission(resource="assets", subresource="servers", action="read"))
    db_session.flush()

    db_session.add(Permission(resource="assets", subresource="servers", action="read"))
    with pytest.raises(IntegrityError):
        db_session.flush()
