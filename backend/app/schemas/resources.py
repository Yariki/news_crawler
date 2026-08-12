
from app.core.rbac import Resources, Actions
from app.schemas.common import StrictModel

class ResourceDefinition(StrictModel):
    resource: Resources
    actions: list[Actions]