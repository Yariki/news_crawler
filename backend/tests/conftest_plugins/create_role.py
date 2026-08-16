from operator import is_
from typing import Any, Awaitable, Callable

import pytest

from app.schemas.role_models import RoleCreateUpdate




@pytest.fixture(name="create_role")
def create_role(faker) -> Callable[[Any], RoleCreateUpdate]:

    def _create_role(**kwargs: dict[Any, Any]) -> RoleCreateUpdate:
        name = kwargs.get("name", faker.word())
        role = RoleCreateUpdate(
            name=name,
            description=kwargs.get("description", faker.sentence()),
            is_system=kwargs.get("is_system", False),
        )
        return role

    return _create_role