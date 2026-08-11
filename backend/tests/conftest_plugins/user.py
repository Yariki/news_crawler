from operator import is_
from typing import Any, Awaitable, Callable

import pytest


from app.schemas.user_models import UserCreate


@pytest.fixture(name="create_user")
def create_user(faker) -> Callable[[Any], UserCreate]:

    def _create_user(**kwargs: dict[Any, Any]) -> UserCreate:
        email = faker.email()
        user = UserCreate(
            email = kwargs.get("email", email),
            username = kwargs.get("username", email),
            password = faker.password(),
            is_active = True
        )
        return user

    return _create_user