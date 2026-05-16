# Security hardening

## Goal
Production-grade security posture for the auth system.

## Tasks
- [ ] Rate limiting with `slowapi`:
  - [ ] `/auth/login`: 5 attempts / minute / IP
  - [ ] `/auth/register`: 3 / hour / IP
  - [ ] `/auth/forgot-password`: 3 / hour / email
- [ ] Account lockout after N consecutive failed logins (e.g. 10 attempts → 15 min lockout)
- [ ] CORS configuration via `fastapi.middleware.cors`:
  - [ ] Explicit allowed origins from env
  - [ ] No wildcard origins in production
- [ ] Security headers middleware:
  - [ ] `Strict-Transport-Security` (HSTS)
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-Frame-Options: DENY`
  - [ ] `Content-Security-Policy` (start in report-only mode)
  - [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] CSRF protection if using cookie-based auth (`fastapi-csrf-protect` or similar)
- [ ] Audit log table and middleware:
  - [ ] Record: actor_id, action, resource_type, resource_id, before/after, timestamp, IP
  - [ ] Log all admin write actions (users, roles, permissions)
  - [ ] Log login success/failure
- [ ] Sensitive config (JWT secret, DB URL) loaded only from env, never committed
- [ ] Generic error messages on login (don't reveal whether email exists)

## Acceptance criteria
- Brute-force login attempts are blocked
- Security headers verified via `securityheaders.com` or equivalent
- Audit log captures all admin actions
- Security review checklist completed
