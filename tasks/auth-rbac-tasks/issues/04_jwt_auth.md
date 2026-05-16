# JWT authentication with access and refresh tokens

## Goal
Implement a complete token-based auth flow with refresh and revocation.

## Tasks
- [ ] Add `python-jose[cryptography]` to dependencies
- [ ] Token helpers in `app/core/security.py`:
  - [ ] `create_access_token(subject, expires_delta)` — short-lived (~15 min)
  - [ ] `create_refresh_token(subject)` — longer-lived (~7 days), includes `jti` for revocation
  - [ ] `decode_token(token) -> TokenPayload`
- [ ] Auth router `app/api/auth.py`:
  - [ ] `POST /auth/register` — creates user, sends verification email (or auto-verifies for now)
  - [ ] `POST /auth/login` — accepts `OAuth2PasswordRequestForm`, returns access + refresh
  - [ ] `POST /auth/refresh` — accepts refresh token, issues new access (+ optionally rotates refresh)
  - [ ] `POST /auth/logout` — revokes refresh token's `jti`
  - [ ] `GET /auth/me` — returns current user (uses dependency from issue 5)
- [ ] Redis-based refresh-token blocklist for revocation (or DB table if Redis unavailable)
- [ ] Config: `JWT_SECRET_KEY`, `JWT_ALGORITHM` (HS256 or RS256), expiry durations from env
- [ ] (Optional) Email verification flow with single-use token

## Acceptance criteria
- Login returns valid access + refresh tokens
- Refresh issues new access token; revoked refresh tokens are rejected
- Logout invalidates the refresh token
- All endpoints documented in OpenAPI
