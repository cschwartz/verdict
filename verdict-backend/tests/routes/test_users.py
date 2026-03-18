from httpx import AsyncClient

from tests.factories.user import RoleFactory, UserFactory, UserRoleFactory


async def test_list_users(app_client: AsyncClient, db_session):
    UserFactory.create()
    UserFactory.create()

    response = await app_client.get("/users/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 2
    assert data["total"] == 2


async def test_list_users_pagination(app_client: AsyncClient, db_session):
    UserFactory.create()
    UserFactory.create()
    UserFactory.create()

    response = await app_client.get("/users/?offset=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 1
    assert data["total"] == 3


async def test_get_user_by_id(app_client: AsyncClient, db_session):
    user = UserFactory.create()

    response = await app_client.get(f"/users/{user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user.username


async def test_get_user_returns_roles(app_client: AsyncClient, db_session):
    user = UserFactory.create()
    role = RoleFactory.create()
    UserRoleFactory.create(user_id=user.id, role_id=role.id)

    response = await app_client.get(f"/users/{user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["roles"] == [role.name]


async def test_get_user_not_found(app_client: AsyncClient, db_session):
    response = await app_client.get("/users/99999")

    assert response.status_code == 404
