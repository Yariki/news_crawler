# Vue Router guards for auth and permissions

## Goal
Declarative route protection by authentication, role, and permission.

## Tasks
- [ ] Define route `meta` schema:
  ```ts
  meta: {
    requiresAuth?: boolean,
    roles?: string[],         // user must have any of these
    permissions?: string[],   // user must have all of these
  }
  ```
- [ ] Global `router.beforeEach` guard:
  - [ ] If `requiresAuth` and not authenticated → redirect `/login?returnUrl=...`
  - [ ] If `roles` set and user has none → redirect `/403`
  - [ ] If `permissions` set and user is missing any → redirect `/403`
- [ ] Wait for `authStore.initFromStorage()` before first navigation
- [ ] `403` and `404` view components
- [ ] Annotate all existing routes with appropriate `meta`

## Acceptance criteria
- Unauthenticated access to protected routes redirects to login
- Insufficient permissions land the user on `/403`
- After login, user is sent to the originally requested URL
