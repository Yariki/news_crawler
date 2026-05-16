# `get_current_user` FastAPI dependency

## Goal
Reusable dependency that resolves the authenticated user from a JWT.

## Tasks
- [ ] Create `OAuth2PasswordBearer` scheme pointing at `/auth/login`
- [ ] `get_current_user` dependency:
  - [ ] Decode JWT, raise 401 on invalid/expired
  - [ ] Load user from DB by subject
  - [ ] Raise 401 if user not found
- [ ] `get_current_active_user` — additionally checks `is_active`, raises 403 if inactive
- [ ] `get_optional_user` — returns `None` if no token (for public-or-personalized endpoints)
- [ ] Eager-load user roles and permissions to avoid N+1
- [ ] Proper 401 responses include `WWW-Authenticate: Bearer` header

## Acceptance criteria
- Endpoints using `Depends(get_current_active_user)` require a valid bearer token
- Swagger UI shows the "Authorize" button and works end-to-end
- Tests cover: valid token, expired token, missing token, inactive user
