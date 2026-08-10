
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import PermissionGranted
from app.db.scope_filter import filter_owned_resources

class BaseAuthRepository:
    
    __abstract__ = True
    
    def __init__(self, db: AsyncSession, access_control: PermissionGranted) -> None:
        self.db = db
        self.access_control = access_control
        
    def filter_owned_resources(self, query, model):
        """
        Filters the query to only include resources owned by the authenticated user.
        
        Args:
            query: The SQLAlchemy query object.
            model: The SQLAlchemy model class.
            owner_attr (str): The name of the owner attribute in the model. Defaults to "owner_id".
        
        Returns:
            The filtered query.
        """
        return filter_owned_resources(query=query, user_id=self.access_control.auth.user_id, model=model, access_control=self.access_control)