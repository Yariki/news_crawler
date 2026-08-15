import re
from app.core.rbac import Resources, Actions, ScopeMode


def validate_password(password: str) -> None:
    """Validate password complexity requirements."""
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[^\w\s]", password):
        raise ValueError("Password must contain at least one special character")


def validate_resources(resource: str) -> None:
    """Validate resource name against allowed resources."""
    
    if resource is None:
        raise ValueError("Resource name cannot be None.")
    if not isinstance(resource, str):
        raise ValueError("Resource name must be a string.")
    if not Resources.has_value(resource):
        raise ValueError(f"Invalid resource name: {resource}")


def validate_actions(action: str) -> None:
    """Validate action name against allowed actions."""
    
    if action is None:
        raise ValueError("Action name cannot be None.")
    if not isinstance(action, str):
        raise ValueError("Action name must be a string.")
    if not Actions.has_value(action):
        raise ValueError(f"Invalid action name: {action}")
    
def validate_scope(scope: str) -> None:
    """Validate scope name against allowed scopes."""
    
    if scope is None:
        raise ValueError("Scope name cannot be None.")
    if not isinstance(scope, str):
        raise ValueError("Scope name must be a string.")
    if not ScopeMode.has_value(scope):
        raise ValueError(f"Invalid scope name: {scope}")
    