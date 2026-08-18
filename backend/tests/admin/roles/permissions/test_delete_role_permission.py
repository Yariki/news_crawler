
from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.role_models import PermissionCreateUpdate, RoleCreateUpdate
from tests.conftest import set_authorization_context

async def test_delete_role_permission_success(
    client: AsyncClient,
    create_role: Callable[..., RoleCreateUpdate],
    create_permission: Callable[..., PermissionCreateUpdate],
    db_session: AsyncSession,
):

    _ = await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")
    permission = create_permission(resource="source", action="create", scope="own")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    role_id = str(response.json()['id'])
    response_per = await client.post(f"/admin/roles/{role_id}/permissions", json=permission.model_dump(mode='json'))
    assert response_per.status_code == 201
    permission_id = response_per.json()['id']

    # Act

    del_resp = await client.delete(f"/admin/roles/{role_id}/permissions/{permission_id}")

    # Assert

    assert del_resp.status_code == 204


async def test_delete_role_permission_role_not_found(
    client: AsyncClient,
    create_role: Callable[..., RoleCreateUpdate],
    create_permission: Callable[..., PermissionCreateUpdate],
    db_session: AsyncSession,
):

    _ = await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")
    permission = create_permission(resource="source", action="create", scope="own")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    role_id = response.json()['id']
    role_id_not_exist = '0af9fc88-f028-4a26-820a-91a4d7d0232a'
    response_per = await client.post(f"/admin/roles/{role_id}/permissions", json=permission.model_dump(mode='json'))
    assert response_per.status_code == 201
    permission_id = response_per.json()['id']

    # Act

    del_resp = await client.delete(f"/admin/roles/{role_id_not_exist}/permissions/{permission_id}")

    # Assert

    assert del_resp.status_code == 404


async def test_delete_role_permission_permission_not_found(
    client: AsyncClient,
    create_role: Callable[..., RoleCreateUpdate],
    create_permission: Callable[..., PermissionCreateUpdate],
    db_session: AsyncSession,
):

    _ = await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")
    permission = create_permission(resource="source", action="create", scope="own")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    role_id = response.json()['id']
    response_per = await client.post(f"/admin/roles/{role_id}/permissions", json=permission.model_dump(mode='json'))
    assert response_per.status_code == 201
    permission_id = '0af9fc88-f028-4a26-820a-91a4d7d0232a' # not exist

    # Act

    del_resp = await client.delete(f"/admin/roles/{role_id}/permissions/{permission_id}")

    # Assert

    assert del_resp.status_code == 404
