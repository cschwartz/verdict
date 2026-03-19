from httpx import AsyncClient

from tests.factories.user import PermissionFactory, RoleFactory, RolePermissionFactory


async def test_list_roles(app_client: AsyncClient, db_session):
    RoleFactory.create()
    RoleFactory.create()

    response = await app_client.get("/roles/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["roles"]) == 2
    assert data["total"] == 2


async def test_get_role_by_id(app_client: AsyncClient, db_session):
    role = RoleFactory.create()

    response = await app_client.get(f"/roles/{role.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == role.name


async def test_get_role_returns_permissions(app_client: AsyncClient, db_session):
    role = RoleFactory.create()
    permission = PermissionFactory.create()
    RolePermissionFactory.create(role_id=role.id, permission_id=permission.id)

    response = await app_client.get(f"/roles/{role.id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["permissions"]) == 1
    assert data["permissions"][0]["resource"] == permission.resource


async def test_get_role_by_name(app_client: AsyncClient, db_session):
    role = RoleFactory.create()

    response = await app_client.get(f"/roles/by-name/{role.name}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == role.name


async def test_get_role_by_name_not_found(app_client: AsyncClient, db_session):
    response = await app_client.get("/roles/by-name/nonexistent")

    assert response.status_code == 404


async def test_get_role_not_found(app_client: AsyncClient, db_session):
    response = await app_client.get("/roles/99999")

    assert response.status_code == 404
