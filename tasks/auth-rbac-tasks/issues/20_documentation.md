# Documentation

## Goal
Make the auth system understandable for current and future developers, and usable for admins.

## Tasks
- [ ] **README — Auth section**
  - [ ] High-level architecture (JWT flow diagram)
  - [ ] Local setup: env vars, default admin credentials, seeding
  - [ ] How to add a new permission
- [ ] **docs/permission-matrix.md**
  - [ ] Table mapping every permission to what it grants
  - [ ] Default role → permissions mapping
- [ ] **docs/auth-architecture.md**
  - [ ] Token flow (login → access + refresh, refresh-on-401, logout)
  - [ ] Ownership model and when admins bypass it
  - [ ] Diagram (Mermaid) of request lifecycle through auth dependencies
- [ ] **docs/admin-guide.md** (user-facing for admin operators)
  - [ ] How to create a user
  - [ ] How to assign roles
  - [ ] How to create custom roles
  - [ ] How to read the audit log
- [ ] **CHANGELOG / migration notes** for existing users:
  - [ ] How existing data was assigned `owner_id`
  - [ ] Any breaking API changes
- [ ] Code-level: docstrings on `RequirePermissions`, `check_ownership`, `get_current_user`

## Acceptance criteria
- A new developer can set up the project and understand the auth system from README + linked docs
- An admin can perform all common operations using the admin guide
