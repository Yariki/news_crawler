# Changelog

## Auth Migration Notes

### Owner Backfill

Migration `20260729_0027_add_owner_property.py` added `owner_id` to `sources`, `crawl_jobs`, `monitored_keywords`, `outbox_events`, `articles`, and `keyword_hits`. Existing rows were assigned to the seeded user with `username = 'admin'`. The migration fails intentionally if that user does not exist, so seed the admin account before applying it to existing databases.

Migration `20260729_0033_alter_owner_column_to_be_not_null.py` made those `owner_id` columns non-null after the backfill.

### Breaking API Changes

- Protected application endpoints now require `Authorization: Bearer <access_token>`.
- Login returns both access and refresh tokens; clients must call `/auth/refresh` with the current refresh token when the access token expires.
- Refresh tokens rotate on every refresh. Clients must replace the stored refresh token with the returned one; reusing an old refresh token is rejected.
- Logout requires the refresh token body: `{"refresh_token":"..."}`.
- Non-admin users need role permissions such as `source:read:own`, `article:read:own`, and `dashboard:read:own` before they can use protected app screens.
