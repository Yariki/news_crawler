# Ownership-based authorization helper

## Goal
A reusable pattern for "users can act on their own resources; admins (or `:any` permission holders) can act on all."

## Tasks
- [ ] `check_ownership(entity, user, any_permission: str | None = None)`:
  - [ ] Allow if `entity.owner_id == user.id`
  - [ ] Allow if `user.has_permission(any_permission)` (e.g. `posts:read:any`)
  - [ ] Otherwise raise 403
- [ ] Query helper `filter_owned(query, model, user, any_permission)`:
  - [ ] If user has `:any` perm → no filter
  - [ ] Else → `WHERE owner_id = user.id`
- [ ] Auto-set `owner_id = current_user.id` on entity creation (service-layer helper)
- [ ] Document the pattern with a working example in the codebase

## Acceptance criteria
- A regular user can only list/edit/delete their own entities
- A user with `<resource>:*:any` permission can access all entities of that type
- Creating an entity automatically assigns the current user as owner
- Tests cover both code paths (own + any)
