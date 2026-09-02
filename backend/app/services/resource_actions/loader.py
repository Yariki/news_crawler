import json

from pydantic import TypeAdapter, ValidationError


from app.core.rbac import Resources
from app.schemas.resources import ResourceDefinition
from app.services.resource_actions.resource_actions import RESOURCE_ACTIONS

import logging

logger = logging.getLogger(__name__)


class PermissionsCatalog:

    def __init__(self, definitions: list[ResourceDefinition]):
        
        if not definitions:
            raise ValueError("Definitions list cannot be empty.")
        
        by_resource: dict[str, ResourceDefinition] = {}
        
        for definition in definitions:
            if definition.resource in by_resource:
                raise ValueError(f"Duplicate resource definition for: {definition.resource}")
            by_resource[definition.resource] = definition
        self._by_resource = by_resource
        self._definitions = definitions
    
    @classmethod
    def load_resource_actions(cls) -> "PermissionsCatalog":
        try:
            data = RESOURCE_ACTIONS
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in RESOURCE_ACTIONS: {e}")
        
        if not isinstance(data, dict) or "permissions" not in data or not isinstance(data["permissions"], list):
            raise ValueError(f"Invalid structure in RESOURCE_ACTIONS: 'permissions' key is missing or not a list.")
        
        try:
            definitions = TypeAdapter(list[ResourceDefinition]).validate_python(data["permissions"])
        except ValidationError as e:
            raise ValueError(f"Invalid resource definitions in RESOURCE_ACTIONS: {e}")
        
        return cls(definitions)
        
    
    @property
    def definitions(self) -> list[ResourceDefinition]:        
        return self._definitions

    def get_definition(self, resource: Resources) -> ResourceDefinition | None:
        return self._by_resource.get(resource)