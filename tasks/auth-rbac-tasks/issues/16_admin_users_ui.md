# Admin Users management UI

## Goal
Full UI for managing users from the admin panel.

## Tasks
- [ ] `UsersListView.vue`
  - [ ] Data table: email, username, roles (chips), status, last login, actions
  - [ ] Search (debounced), filter by role/status, pagination
  - [ ] Sort by column
- [ ] `UserCreateDialog.vue` — modal/drawer to create a user with initial roles
- [ ] `UserEditView.vue` — full edit page with tabs (Profile, Roles, Sessions)
  - [ ] Profile tab: update email, username, status
  - [ ] Roles tab: multi-select role assignment
  - [ ] Reset password button (confirm dialog → calls admin reset endpoint)
- [ ] Activate/deactivate toggle in list view (with confirm)
- [ ] Confirmation dialogs for all destructive actions
- [ ] Optimistic UI updates where safe; rollback on error

## Acceptance criteria
- All admin user-management API endpoints have corresponding UI
- Self-protection: admin cannot deactivate or demote themselves (UI disables the actions)
- Loading, error, and empty states implemented
