

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from tests.conftest import set_authorization_context

async def test_assign_role_to_user_success(client, create_user, create_role, db_session):
    
    await set_authorization_context(
        db_session,
        "*:*:*",
        user_name="admin",
    )

    # Arrange
    user = create_user()
    role1 = create_role(name="supervisor")
    role2 = create_role(name="manager2")
    response_user = await client.post("/admin/users", json=user.model_dump(mode='json'))
    response1 = await client.post("/admin/roles", json=role1.model_dump(mode='json'))
    response2 = await client.post("/admin/roles", json=role2.model_dump(mode='json'))
    user_id = response_user.json()["id"]
    role_ids = [response1.json()["id"], response2.json()["id"]]
    response_assign_roles = await client.post(f"/admin/users/{user_id}/roles", json={"roles_ids": role_ids})
    assert response_assign_roles.status_code == 200
    
    # Act
    
    response = await client.get(f"/admin/users/{user_id}/roles")

    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2    