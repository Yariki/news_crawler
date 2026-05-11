# Authentication and Authorization Implementation Tasks

## 1) Discovery and Design
- [ ] Inventory all backend entities and API endpoints that need ownership and access control.
- [ ] Define authorization model (RBAC scopes, role hierarchy, and admin permissions).
- [ ] Define authentication flow for backend and Vue app (login, token refresh, logout, session expiration).
- [ ] Define migration strategy for existing records when `owner_id` becomes required.

## 2) Database and Domain Model Changes
- [ ] Add `users` entity (id, email/username, password hash, status, timestamps, audit fields).
- [ ] Add `roles` entity and `user_roles` association table for many-to-many assignment.
- [ ] Add `owner_id` to all owned domain entities (sources, monitored keywords, articles, crawl jobs, keyword hits, and other persisted business entities).
- [ ] Add foreign keys and indexes for `owner_id`, `user_id`, and role mapping tables.
- [ ] Update SQLAlchemy models, relationships, and constraints to reflect users/roles/ownership.
- [ ] Create and test Alembic migrations for schema and data backfill.

## 3) Backend Authentication
- [ ] Add secure password hashing and verification service.
- [ ] Implement auth endpoints (`register` if required, `login`, `refresh`, `logout`, `me`).
- [ ] Implement JWT/session token generation, validation, rotation, and expiration handling.
- [ ] Add dependency/middleware to resolve current authenticated user from request context.
- [ ] Add auth error handling strategy (unauthenticated vs unauthorized responses).

## 4) Backend Authorization and Ownership Enforcement
- [ ] Add reusable permission checks for role-based access.
- [ ] Enforce `owner_id` filtering in repositories/services so users only access owned data unless admin.
- [ ] Enforce ownership assignment on create operations using current user.
- [ ] Add admin bypass rules where required for support/operations actions.
- [ ] Protect sensitive routes (user/role management, global operations) with admin-only permissions.
- [ ] Review websocket and background jobs for tenant/owner isolation requirements.

## 5) Admin APIs
- [ ] Add APIs for user management (list, create, update status, reset credentials as needed).
- [ ] Add APIs for role management (CRUD roles and role-permission mapping).
- [ ] Add APIs for assigning/removing roles from users.
- [ ] Add pagination, filtering, and auditing fields for admin management endpoints.

## 6) Frontend Authentication and Route Guards (Vue)
- [ ] Add auth store for current user, tokens/session state, and derived permissions.
- [ ] Add login/logout UX and session restoration on app load.
- [ ] Add authenticated Axios/interceptor flow (attach token, refresh on expiry, fallback to login).
- [ ] Add route guards for authenticated-only pages and role-protected pages.
- [ ] Add unauthorized/forbidden UX states.

## 7) Frontend Admin Panel (Users and Roles)
- [ ] Add admin navigation entry and dedicated admin layout/pages.
- [ ] Build user management page (list/search/filter/create/edit/activate/deactivate).
- [ ] Build role management page (list/create/edit/delete and permissions matrix if used).
- [ ] Build user-role assignment UI.
- [ ] Add frontend validation, loading/error states, and optimistic update handling where appropriate.

## 8) Security, Audit, and Operations
- [ ] Add brute-force protection/rate limits for auth endpoints.
- [ ] Add audit logging for auth events and admin changes (user/role updates).
- [ ] Add secure defaults for CORS, cookie/token transport, and secret management.
- [ ] Validate background scheduler and scraper flows under authenticated/owned data model.

## 9) Tests and Validation
- [ ] Add backend unit/integration tests for auth, RBAC checks, and owner isolation.
- [ ] Add migration tests for backfilled ownership and role assignments.
- [ ] Add frontend tests for route guards, auth store behavior, and admin flows.
- [ ] Add end-to-end scenarios: normal user isolation, admin access, and forbidden operations.
- [ ] Run full regression for existing source/keywords/dashboard features under ownership constraints.

## 10) Rollout and Documentation
- [ ] Document role model, permission matrix, and ownership rules.
- [ ] Document environment variables/secrets required for auth.
- [ ] Prepare phased rollout checklist (feature flags, admin bootstrap user, rollback steps).
- [ ] Define post-deploy verification checks and monitoring alerts for auth failures.
