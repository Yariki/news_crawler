# Admin Roles and Permissions UI

## Goal
UI for managing roles and their permission assignments.

## Tasks
- [ ] `RolesListView.vue` — list of all roles with assigned permission count and user count
- [ ] `RoleCreateDialog.vue` — create new role (name, description)
- [ ] `RoleEditView.vue`
  - [ ] Edit role metadata
  - [ ] Permission picker:
    - [ ] Permissions grouped by resource (collapsible sections)
    - [ ] Checkbox per permission
    - [ ] "Select all" per group
    - [ ] Live search
  - [ ] List of users assigned to this role (link to user edit)
  - [ ] Delete role button (disabled for system roles, disabled if users assigned)
- [ ] Visual indication of system roles (badge, lock icon)
- [ ] Save changes with a single "Save" action; show pending changes

## Acceptance criteria
- All role/permission API endpoints have UI coverage
- System roles are clearly marked and protected in the UI
- Permission picker is usable even with 50+ permissions
