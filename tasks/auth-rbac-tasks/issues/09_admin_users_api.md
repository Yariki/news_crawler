# Admin User management API

## Goal
Endpoints for admins to manage user accounts.

## Endpoints (all under `/admin/users`, gated by `users:admin` permission)
- [ ] `GET /admin/users` — list with pagination (`page`, `size`), search (`q`), filters (`role`, `is_active`)
- [ ] `GET /admin/users/{id}` — full user details including roles
- [ ] `POST /admin/users` — create user (admin can create with arbitrary roles)
- [ ] `PUT /admin/users/{id}` — update profile fields
- [ ] `DELETE /admin/users/{id}` — soft delete (`is_active = false`)
- [ ] `POST /admin/users/{id}/activate` — re-enable
- [ ] `POST /admin/users/{id}/roles` — assign roles (body: `{role_ids: [...]}`)
- [ ] `DELETE /admin/users/{id}/roles/{role_id}` — remove a role
- [ ] `POST /admin/users/{id}/reset-password` — generate temp password OR send reset email

## Cross-cutting
- [ ] Audit log: every admin write action recorded (see issue 19)
- [ ] Prevent admin from removing their own admin role / deactivating themselves
- [ ] Prevent deletion of the last admin user

## Acceptance criteria
- All endpoints return 403 for non-admins
- Pagination and search work correctly
- Self-protection rules enforced
- Integration tests cover happy path + edge cases
