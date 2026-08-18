from tests.conftest import set_authorization_context


async def test_delete_role_success(client, create_role, db_session):

    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    assert response.status_code == 201
    role_id = response.json()['id']

    # Act
    response = await client.delete(f"/admin/roles/{role_id}")

    # Assert
    assert response.status_code == 204


async def test_delete_role_not_found(client, create_role, db_session):

    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role_id = '00000000-0000-0000-0000-000000000000'

    # Act
    response = await client.delete(f"/admin/roles/{role_id}")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == f"Role with ID '{role_id}' not found."
