from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from fastapi import HTTPException
import pytest

from app.core.security import hash_password
from app.schemas.user_models import UserCreate, UserUpdate
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_create_user_persists_unique_user_and_returns_read_model(monkeypatch):
    """A unique user is hashed, persisted, refreshed, and returned."""
    db_session = AsyncMock()
    db_session.execute.side_effect = [
        Mock(scalar_one_or_none=Mock(return_value=None)),
        Mock(scalar_one_or_none=Mock(return_value=None)),
    ]
    user_id = uuid4()

    async def refresh_user(user):
        user.id = user_id
        user.is_verified = False
        user.last_login_at = None

    db_session.refresh.side_effect = refresh_user
    hash_password = Mock(return_value="hashed-password")
    monkeypatch.setattr("app.services.user_service.hash_password", hash_password)
    user_create = UserCreate(
        email="person@example.com",
        username="person",
        password="SafePassword1!",
        is_active=True,
    )

    created_user = await UserService(db_session).create_user(user_create)

    hash_password.assert_called_once_with(user_create.password)
    db_session.execute.assert_awaited()
    assert db_session.execute.await_count == 2
    db_session.add.assert_called_once()
    persisted_user = db_session.add.call_args.args[0]
    assert persisted_user.email == user_create.email
    assert persisted_user.username == user_create.username
    assert persisted_user.hashed_password == "hashed-password"
    assert persisted_user.is_active is True
    db_session.commit.assert_awaited_once()
    db_session.refresh.assert_awaited_once_with(persisted_user)
    assert created_user.id == user_id
    assert created_user.email == user_create.email
    assert created_user.username == user_create.username
    assert created_user.is_active is True
    assert created_user.is_verified is False
    assert created_user.last_login_at is None


@pytest.mark.asyncio
async def test_create_user_raises_http_exception_for_non_unique_email():
    """An HTTPException is raised if the email is already in use."""
    db_session = AsyncMock()
    db_session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=Mock()))
    user_create = UserCreate(
        email="person@example.com",
        username="person",
        password="SafePassword1!",
        is_active=True,
    )
    with pytest.raises(Exception):
        await UserService(db_session).create_user(user_create)

@pytest.mark.asyncio
async def test_create_user_raises_http_exception_for_non_unique_username():
    """An HTTPException is raised if the username is already in use."""
    db_session = AsyncMock()
    db_session.execute.side_effect = [
        Mock(scalar_one_or_none=Mock(return_value=None)),
        Mock(scalar_one_or_none=Mock(return_value=Mock())),
    ]
    user_create = UserCreate(
        email="person@example.com",
        username="person",
        password="SafePassword1!",
        is_active=True,
    )
    with pytest.raises(Exception):
        await UserService(db_session).create_user(user_create)



@pytest.mark.asyncio
async def test_get_by_email_returns_user_read_model_for_existing_user():
    db_session = AsyncMock()
    user_id = uuid4()
    db_session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=Mock(
        id=user_id,
        email="person@example.com",
        username="person",
        hashed_password="hashed-password",
        is_active=True,
        is_verified=False,
        last_login_at=None,
    )))
    from app.services.user_service import UserService
    user = await UserService(db_session).get_by_email("person@example.com")
    assert user.id == user_id
    assert user.email == "person@example.com"
    assert user.username == "person"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.last_login_at is None


@pytest.mark.asyncio
async def test_get_by_email_fails():
    db_session = AsyncMock()
    user_id = uuid4()
    db_session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=None))
    from app.services.user_service import UserService
    
    with pytest.raises(HTTPException):
        await UserService(db_session).get_by_email("person@example.com")


@pytest.mark.asyncio
async def test_get_by_id_returns_user_read_model_for_existing_user():
    db_session = AsyncMock()
    user_id = uuid4()
    db_session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=Mock(
        id=user_id,
        email="person@example.com",
        username="person",
        hashed_password="hashed-password",
        is_active=True,
        is_verified=False,
        last_login_at=None,
    )))
    from app.services.user_service import UserService
    user = await UserService(db_session).get_by_id(user_id)
    assert user.id == user_id
    assert user.email == "person@example.com"
    assert user.username == "person"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.last_login_at is None


@pytest.mark.asyncio
async def test_get_by_id_fails():
    db_session = AsyncMock()
    user_id = uuid4()
    db_session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=None))
    from app.services.user_service import UserService
    
    with pytest.raises(HTTPException):
        await UserService(db_session).get_by_id(user_id)

@pytest.mark.asyncio
async def test_authenticate_returns_user_for_valid_credentials():
    db_session = AsyncMock()
    user_id = uuid4()
    db_session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=Mock(
        id=user_id,
        email="person@example.com",
        username="person",
        hashed_password=hash_password("hashed-password"),
        is_active=True,
        is_verified=False,
        last_login_at=None,
    )))
    from app.services.user_service import UserService
    user = await UserService(db_session).authenticate("person", "hashed-password")
    assert user.id == user_id
    assert user.email == "person@example.com"
    assert user.username == "person"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.last_login_at is None


@pytest.mark.asyncio
async def test_authenticate_raises_http_exception_for_invalid_credentials():
    db_session = AsyncMock()
    user_id = uuid4()
    db_session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=Mock(
        id=user_id,
        email="person@example.com",
        username="person",
        hashed_password=hash_password("hashed-password"),
        is_active=True,
        is_verified=False,
        last_login_at=None,
    )))
    from app.services.user_service import UserService
    with pytest.raises(HTTPException):
        await UserService(db_session).authenticate("person", "wrong-password")


@pytest.mark.asyncio
async def test_authenticate_raises_http_exception_for_user_mot_found():
    db_session = AsyncMock()
    user_id = uuid4()
    db_session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=None))
    from app.services.user_service import UserService
    with pytest.raises(HTTPException):
        await UserService(db_session).authenticate("person", "wrong-password")


@pytest.mark.asyncio
async def test_authenticate_update_user():
    db_session = AsyncMock()
    user_id = uuid4()
    persisted_user = Mock(
        id=user_id,
        email="person@example.com",
        username="person",
        hashed_password=hash_password("hashed-password"),
        is_active=True,
        is_verified=False,
        last_login_at=None,
    )
    db_session.execute.side_effect = [
        Mock(scalar_one_or_none=Mock(return_value=None)),
        Mock(scalar_one_or_none=Mock(return_value=None)),
        Mock(scalar_one_or_none=Mock(return_value=persisted_user)),
    ]
    
    def refresh_user(user):
        user.username = "updated-person"
        user.email = "updated-person@example.com"
        
    
    db_session.refresh.side_effect = refresh_user
    
    userUpdated = UserUpdate(
        email="user@updated.com",
        username="updated-person",
    )
    user = await UserService(db_session).update_user(user_id, userUpdated)
    
    db_session.execute.assert_awaited()
    db_session.commit.assert_awaited_once()
    db_session.refresh.assert_awaited_once_with(persisted_user)
    assert user.username == "updated-person"
    assert user.email == "updated-person@example.com"


@pytest.mark.asyncio
async def test_authenticate_update_user_email_not_unique():
    db_session = AsyncMock()
    user_id = uuid4()
    persisted_user = Mock(
        id=user_id,
        email="person@example.com",
        username="person",
        hashed_password=hash_password("hashed-password"),
        is_active=True,
        is_verified=False,
        last_login_at=None,
    )
    db_session.execute.side_effect = [
        Mock(scalar_one_or_none=Mock(return_value=Mock(
            id=uuid4(),
            email="other@example.com",
            username="other-person",
            hashed_password=hash_password("hashed-password"),
            is_active=True,
            is_verified=False,
            last_login_at=None,
        ))),
        Mock(scalar_one_or_none=Mock(return_value=None)),
        Mock(scalar_one_or_none=Mock(return_value=persisted_user)),
    ]
    
    def refresh_user(user):
        user.username = "updated-person"
        user.email = "updated-person@example.com"
        
    
    db_session.refresh.side_effect = refresh_user

    with pytest.raises(HTTPException):
        userUpdated = UserUpdate(
            email="updated-person@example.com",
            username="other-person",
        )
        await UserService(db_session).update_user(user_id, userUpdated)
    


@pytest.mark.asyncio
async def test_authenticate_update_user_username_not_unique():
    db_session = AsyncMock()
    user_id = uuid4()
    persisted_user = Mock(
        id=user_id,
        email="person@example.com",
        username="person",
        hashed_password=hash_password("hashed-password"),
        is_active=True,
        is_verified=False,
        last_login_at=None,
    )
    db_session.execute.side_effect = [
        Mock(scalar_one_or_none=Mock(return_value=None)),
        Mock(scalar_one_or_none=Mock(return_value=Mock(
            id=uuid4(),
            email="other@example.com",
            username="other-person",
            hashed_password=hash_password("hashed-password"),
            is_active=True,
            is_verified=False,
            last_login_at=None,
        ))),
        Mock(scalar_one_or_none=Mock(return_value=persisted_user)),
    ]
    
    def refresh_user(user):
        user.username = "updated-person"
        user.email = "updated-person@example.com"
        
    
    db_session.refresh.side_effect = refresh_user

    with pytest.raises(HTTPException):
        userUpdated = UserUpdate(
            email="user@updated.com",
            username="updated-person",
        )
        await UserService(db_session).update_user(user_id, userUpdated)


@pytest.mark.asyncio
async def test_update_last_login_at():  
    db_session = AsyncMock()
    user_id = uuid4()
    persisted_user = Mock(
        id=user_id,
        email="person@example.com",
        username="person",
        hashed_password=hash_password("hashed-password"),
        is_active=True,
        is_verified=False,
        last_login_at=None,
    )
    db_session.execute.side_effect = [
        Mock(scalar_one_or_none=Mock(return_value=persisted_user)),
    ]
    from app.services.user_service import UserService
    user = await UserService(db_session).update_last_login_at(user_id)
    db_session.execute.assert_awaited()
    db_session.commit.assert_awaited_once()
    db_session.refresh.assert_awaited_once_with(persisted_user)
    assert user.last_login_at is not None
    