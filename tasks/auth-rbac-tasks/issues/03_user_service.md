# Password hashing and User service

## Goal
Secure password storage and a clean service layer for user operations.

## Tasks
- [ ] Add `passlib[bcrypt]` (or `argon2-cffi`) to dependencies
- [ ] Create `app/core/security.py` with `hash_password()` and `verify_password()`
- [ ] Create `app/services/user_service.py` with:
  - [ ] `create_user(data: UserCreate) -> User`
  - [ ] `get_by_email(email) -> User | None`
  - [ ] `get_by_id(id) -> User | None`
  - [ ] `authenticate(email, password) -> User | None`
  - [ ] `update_user(user, data: UserUpdate) -> User`
  - [ ] `deactivate(user)` (soft delete via `is_active=False`)
  - [ ] `update_last_login(user)`
- [ ] Pydantic schemas: `UserCreate`, `UserRead`, `UserUpdate`, `UserInDB`
- [ ] Password validator: min 8 chars, at least one digit, one letter (configurable)
- [ ] Never expose `password_hash` in any response schema

## Acceptance criteria
- Passwords stored as bcrypt/argon2 hashes only
- `authenticate()` returns `None` for invalid credentials or inactive users
- Unit tests cover all service methods
