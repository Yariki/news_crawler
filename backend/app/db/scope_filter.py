
from sqlalchemy import ColumnElement, Select
from uuid import UUID
from app.core.rbac import PermissionGranted
from app.db.base import OwnerMixin


def filter_owned_resources(*, query: Select, user_id: UUID, model: OwnerMixin, access_control: PermissionGranted) -> Select:
    """
    Filters the query to only include resources owned by the specified user.

    Args:
        query: The SQLAlchemy query object.
        user_id (UUID): The ID of the user.
        model (OwnerMixin): The SQLAlchemy model class.
        access_control (PermissionGranted): The access control object.
        owner_attr (str): The name of the owner attribute in the model. Defaults to "owner_id".

    Returns:
        The filtered query.
    """
    if access_control.is_any:
        return query
    
    return query.where(model.owner_id == user_id)