# Apply authentication and authorization to existing endpoints

## Goal
Retrofit all current endpoints with auth, ownership filtering, and permission checks.

## Tasks
- [ ] Audit all existing routes — produce a checklist mapping each route to required auth/permission
- [ ] Add `Depends(get_current_active_user)` to every protected endpoint
- [ ] Apply `filter_owned()` to list endpoints
- [ ] Apply `check_ownership()` to detail/update/delete endpoints
- [ ] Set `owner_id = current_user.id` on create endpoints
- [ ] Update Pydantic response schemas (don't expose other users' data leakage via relations)
- [ ] Verify OpenAPI docs reflect new auth requirements (FastAPI does this automatically with `Depends`)

## Acceptance criteria
- No protected endpoint is reachable without a valid token
- Users cannot see/modify/delete resources owned by other users (unless they have `:any` permission)
- All endpoints have explicit auth dependencies declared
