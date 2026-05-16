# Add `owner_id` to all existing entities

## Goal
Every domain entity should track its owner for ownership-based authorization.

## Tasks
- [ ] Audit all existing SQLAlchemy models — produce a list of tables that need `owner_id`
- [ ] Add `owner_id: UUID FK -> users.id` to each model (nullable initially)
- [ ] Write a backfill migration:
  - [ ] Decide policy: assign existing records to a system admin user, or to creator if there's a `created_by` field
  - [ ] Document the chosen policy in the migration
- [ ] Run backfill, then alter column to `NOT NULL`
- [ ] Add SQLAlchemy `relationship("User", back_populates="...")` both directions
- [ ] Add indexes on `owner_id` for query performance
- [ ] Update Pydantic schemas to expose `owner_id` where appropriate (read-only)

## Acceptance criteria
- All entity tables have `owner_id NOT NULL` with FK constraint
- All existing rows have a valid `owner_id`
- ORM queries can eagerly load `entity.owner`
