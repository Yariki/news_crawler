from operator import is_
from typing import Any, Awaitable, Callable

import pytest

from app.models import User


@pytest.fixture(name="create_user")
def create_user(faker) -> Callable[[Any], Awaitable[User]]:

    async def _create_user(**kwargs: dict[Any, Any]) -> User:
        email = faker.email()
        user = User(
            email = email,
            username = email,
            hashed_password=faker.password(),
            is_active = True,
            is_verified = True
        )
        return user

    return _create_user