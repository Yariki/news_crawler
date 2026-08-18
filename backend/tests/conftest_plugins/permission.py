from typing import Any, Callable

import pytest

from app.schemas.role_models import PermissionCreateUpdate


@pytest.fixture(name="create_permission")
def create_permission(faker) -> Callable[..., PermissionCreateUpdate]:

    def _create_permission(**kwargs: Any) -> PermissionCreateUpdate:
        scope = kwargs.get("scope", "own")
        resource = kwargs.get("resource", "source")
        action = kwargs.get("action", "create")
        name = f"{resource}:{action}:{scope}"
        role = PermissionCreateUpdate(
            name=name,
            description=kwargs.get("description", faker.sentence()),
            resource=resource,
            action=action,
            scope=scope
        )
        return role

    return _create_permission
