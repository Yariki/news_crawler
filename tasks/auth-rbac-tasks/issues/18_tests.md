# Tests: auth, RBAC, ownership, admin flows

## Goal
Comprehensive test coverage for the auth & authorization system.

## Backend (pytest + FastAPI TestClient)
- [ ] Unit tests for `security.py` (password hashing, token create/decode)
- [ ] Unit tests for `UserService` (create, authenticate, etc.)
- [ ] Unit tests for `RequirePermissions` / `RequireRoles` dependencies
- [ ] Unit tests for `check_ownership` and `filter_owned`
- [ ] Integration tests for `/auth/*` endpoints (register, login, refresh, logout)
- [ ] Integration tests for `/admin/users/*` and `/admin/roles/*`
- [ ] Test ownership enforcement on a sample entity endpoint
- [ ] Test that admin can access any resource; regular users only their own
- [ ] Fixtures: factory for users with arbitrary roles/permissions

## Frontend (Vitest + Vue Test Utils)
- [ ] Auth store actions and getters
- [ ] Login form validation and submission
- [ ] Router guard behavior (mock authenticated/unauthenticated states)
- [ ] Permission-gated UI components hide/show correctly

## E2E (Playwright or Cypress)
- [ ] User registers → logs in → accesses profile
- [ ] Admin logs in → creates user → assigns role → user can log in with new role
- [ ] Unauthorized user is redirected from admin routes
- [ ] Token refresh works after access token expires

## Acceptance criteria
- Backend coverage on auth modules ≥ 85%
- E2E suite runs in CI and passes
