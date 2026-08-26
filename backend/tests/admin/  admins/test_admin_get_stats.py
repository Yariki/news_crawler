from tests.conftest import client, client, set_authorization_context


async def test_activate_user_success(client,
                                     create_user,
                                     create_role,
                                     db_session):

    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )
    
    # Arrange
    user = create_user()
    role = create_role(name="supervisor")
    response = await client.post("/admin/users", json=user.model_dump(mode='json'))
    response_role = await client.post("/admin/roles", json=role.model_dump(mode='json'))
    assert response.status_code == 201
    assert response_role.status_code == 201

    user_id = response.json()["id"]
    role_id = response_role.json()["id"]
    
    roled_ids = [role_id]

    response_assign = await client.post(f"/admin/users/{user_id}/roles", json={"roles_ids": roled_ids})
    assert response_assign.status_code == 200    
    
    # Act
    
    response_stats = await client.get("/admin/stats")
    
    # Assert
    assert response_stats.status_code == 200
    data_stats = response_stats.json()
    assert data_stats["total_users"] == 2
    assert data_stats["active_users"] == 2
    assert data_stats["recent_registrations"] == 2
    assert len(data_stats["role_distributions"]) == 1

async def test_activate_user_success(client,
                                     db_session):

    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )
    
    # Arrange
    # Act
    
    response_stats = await client.get("/admin/stats");
    
    # Assert
    assert response_stats.status_code == 200
    data_stats = response_stats.json()
    assert data_stats["total_users"] == 1
    assert data_stats["active_users"] == 1
    assert data_stats["recent_registrations"] == 1
    assert len(data_stats["role_distributions"]) == 0


