# Admin panel layout and dashboard

## Goal
A protected `/admin` section with navigation and an overview dashboard.

## Tasks
- [ ] `AdminLayout.vue` with sidebar (Users, Roles, Permissions, Audit Log) and topbar
- [ ] Nested routes under `/admin`:
  - [ ] `/admin` → dashboard
  - [ ] `/admin/users`
  - [ ] `/admin/roles`
  - [ ] `/admin/audit-log` (if issue 19 is in scope)
- [ ] Route guard: `meta: { requiresAuth: true, roles: ['admin'] }` on the parent
- [ ] Dashboard widgets:
  - [ ] Total users / active users
  - [ ] Recent registrations (last 7 days)
  - [ ] Role distribution (pie chart or simple table)
  - [ ] Recent admin actions (if audit log exists)
- [ ] Responsive layout (sidebar collapses on mobile)

## Acceptance criteria
- Non-admins cannot access any `/admin/*` route
- Dashboard data fetched via dedicated `/admin/stats` endpoint (create as part of this task)
- Navigation works between all admin sections
