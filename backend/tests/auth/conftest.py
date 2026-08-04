from operator import is_
from typing import Any, Awaitable, Callable

import pytest

from app.schemas.user_models import UserCreate, UserRead


@pytest.fixture(name="make_user_create")
def create_user(faker) -> Callable[..., Awaitable[UserCreate]]:

    async def _create_user(password: str, **kwargs: Any) -> UserCreate:
        email = faker.email()
        user = UserCreate(
            email = kwargs.get('email', email),
            username = kwargs.get('username', email),
            password = password,
            is_active = kwargs.get('is_active', True),
        )
        return user

    return _create_user

