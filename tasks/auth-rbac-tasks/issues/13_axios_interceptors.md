# Axios interceptors for auth and token refresh

## Goal
Transparently attach the access token and handle refresh-on-401.

## Tasks
- [ ] Create `lib/axios.ts` with a configured Axios instance
- [ ] Request interceptor: attach `Authorization: Bearer <accessToken>` from auth store
- [ ] Response interceptor on 401:
  - [ ] If the failed request was `/auth/refresh` itself → logout
  - [ ] Otherwise → attempt `authStore.refresh()`, then retry the original request once
  - [ ] If refresh fails → logout and redirect to `/login`
- [ ] Queue concurrent requests during refresh so they don't all trigger parallel refreshes
- [ ] On 403 → optionally show a global toast "You don't have permission"

## Acceptance criteria
- Authenticated requests work without manual token handling
- Expired access tokens are refreshed transparently
- Concurrent 401s during refresh do not cause multiple refresh calls
- Failed refresh cleanly logs the user out
