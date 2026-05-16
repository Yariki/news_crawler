# Permission and role checking dependencies (RBAC)

## Goal
Composable authorization primitives for FastAPI endpoints.

## Tasks
- [ ] `RequirePermissions(*perms, mode="all"|"any")` class-based dependency:
  - [ ] Aggregates permissions from all user roles
  - [ ] `mode="all"` requires all listed perms; `mode="any"` requires at least one
  - [ ] Returns 403 with a list of missing permissions
- [ ] `RequireRoles(*roles)` class-based dependency for role-level checks
- [ ] Cache user permissions on the request object to avoid repeated DB hits
- [ ] Helper `user.has_permission(name)` and `user.has_role(name)` on the User model
- [ ] Document the permission naming convention in code (docstrings) and in README

## Example usage
```python
@router.delete("/posts/{id}", dependencies=[Depends(RequirePermissions("posts:delete:any"))])
async def delete_post(...): ...
```

## Acceptance criteria
- Endpoints reject users missing the required permission with 403
- Admin role (with all permissions) passes every check
- Tests cover: missing perm, has perm, multiple perms `all`/`any`
