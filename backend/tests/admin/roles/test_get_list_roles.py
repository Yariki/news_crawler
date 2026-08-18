from tests.conftest import set_authorization_context

async def test_get_list_role_success(client, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    role = create_role(name="supervisor")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    assert response.status_code == 201
    role = create_role(name="editor")
    response = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    assert response.status_code == 201
    
    # Act
    response2 = await client.get("/admin/roles")

    # Assert
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 5 # because there are 3 default roles in the database, so total 5 roles