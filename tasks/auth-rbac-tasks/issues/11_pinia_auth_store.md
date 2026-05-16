# Pinia auth store (Vue.js)

## Goal
Centralized auth state with token management and permission helpers.

## Tasks
- [ ] Create `stores/auth.ts` (or `.js`) with Pinia
- [ ] State: `user`, `accessToken`, `refreshToken`, `roles`, `permissions`, `isAuthenticated` (getter)
- [ ] Actions:
  - [ ] `login(credentials)` — POST `/auth/login`, store tokens, fetch user
  - [ ] `logout()` — POST `/auth/logout`, clear state
  - [ ] `refresh()` — POST `/auth/refresh`, update access token
  - [ ] `fetchCurrentUser()` — GET `/auth/me`, populate user + roles + permissions
  - [ ] `initFromStorage()` — restore session on app boot
- [ ] Getters: `hasPermission(name)`, `hasRole(name)`, `hasAnyPermission([...])`
- [ ] Storage strategy (pick one and document):
  - Refresh token in `httpOnly` Secure cookie (recommended; backend issues `Set-Cookie`)
  - OR refresh token in localStorage (simpler, less secure)
- [ ] Access token in memory only (never localStorage)

## Acceptance criteria
- `useAuthStore()` provides reactive auth state across the app
- Session survives page reload (via cookie or localStorage)
- Logout clears all auth state and tokens
