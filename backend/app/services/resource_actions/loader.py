import json
from pathlib import Path

from pydantic import TypeAdapter, ValidationError


from app.core.rbac import Resources
from app.schemas.resources import ResourceDefinition


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
    def create_from_file(cls, file_path: Path) -> "PermissionsCatalog":
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        
        if not isinstance(data, dict) or "permissions" not in data or not isinstance(data["permissions"], list):
            raise ValueError(f"Invalid structure in file {file_path}: 'permissions' key is missing or not a list.")
        
        try:
            definitions = TypeAdapter(list[ResourceDefinition]).validate_python(data["permissions"])
        except ValidationError as e:
            raise ValueError(f"Invalid resource definitions in file {file_path}: {e}")
        
        return cls(definitions)
        
    
    @property
    def definitions(self) -> list[ResourceDefinition]:        
        return self._definitions

    def get_definition(self, resource: Resources) -> ResourceDefinition | None:
        return self._by_resource.get(resource)