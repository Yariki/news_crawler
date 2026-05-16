# Admin Role and Permission management API

## Goal
Endpoints for admins to manage roles and the permission assignments.

## Endpoints (gated by `roles:admin` permission)
- [ ] `GET /admin/roles` — list all roles with their permissions
- [ ] `GET /admin/roles/{id}` — role details + assigned users count
- [ ] `POST /admin/roles` — create role
- [ ] `PUT /admin/roles/{id}` — update name/description (block on system roles)
- [ ] `DELETE /admin/roles/{id}` — delete role (block on system roles, block if users assigned)
- [ ] `POST /admin/roles/{id}/permissions` — assign permissions (body: `{permission_ids: [...]}`)
- [ ] `DELETE /admin/roles/{id}/permissions/{permission_id}` — revoke a permission
- [ ] `GET /admin/permissions` — list all available permissions (grouped by resource)
- [ ] `GET /admin/roles/{id}/users` — list users assigned to a role (paginated)

## Cross-cutting
- [ ] System roles (`admin`, `user`) cannot be deleted or renamed
- [ ] Audit log all changes (see issue 19)

## Acceptance criteria
- CRUD works for non-system roles
- System role protection enforced
- Permission catalog is comprehensive
- Tests cover system-role protection
