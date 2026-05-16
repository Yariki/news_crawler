# Set up Alembic and design auth database schema

## Goal
Establish the database foundation for users, roles, and permissions (full RBAC).

## Tasks
- [ ] Configure Alembic for migrations (if not already present)
- [ ] Create `users` table: `id` (UUID PK), `email` (unique), `username` (unique), `password_hash`, `is_active` (bool, default true), `is_verified` (bool, default false), `created_at`, `updated_at`, `last_login_at`
- [ ] Create `roles` table: `id`, `name` (unique), `description`, `is_system` (bool — protect built-ins from deletion)
- [ ] Create `permissions` table: `id`, `name` (e.g. `users:read`, `posts:write:any`), `resource`, `action`, `description`
- [ ] Create `user_roles` join table (`user_id`, `role_id`, PK composite)
- [ ] Create `role_permissions` join table (`role_id`, `permission_id`, PK composite)
- [ ] Seed migration: default roles `admin`, `manager`, `user`; permissions matrix for known resources
- [ ] Seed migration: create initial admin user (env-driven credentials)

## Notes
- Use UUIDs for `user.id` to avoid leaking row counts and to ease distributed scenarios.
- Permission naming convention: `<resource>:<action>[:<scope>]` where scope is `own` or `any`. Example: `posts:read:own`, `posts:read:any`.

## Acceptance criteria
- `alembic upgrade head` creates all tables on a fresh DB
- Default roles and admin user exist after seeding
- Constraints and indexes verified (unique email, unique role name)
