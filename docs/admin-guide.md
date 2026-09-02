# Admin Guide

This guide is for operators using the admin area or the admin API. Sign in with an account that has the `admin` role, then open `/admin`.

## Create A User

In the UI:

1. Open `/admin/users`.
2. Select the add-user action.
3. Enter email, username, password, and active status.
4. Save the user.

API equivalent:

```bash
curl -X POST http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"person@example.com","username":"person","password":"StrongPass123!","is_active":true}'
```

New users do not receive roles automatically. Assign at least one role before expecting them to access protected app features.

## Assign Roles

In the UI:

1. Open `/admin/users`.
2. Find the user.
3. Open the roles action for that row.
4. Select one or more roles.
5. Save.

API equivalent:

```bash
curl -X POST http://localhost:8000/api/admin/users/$USER_ID/roles \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"roles_ids":["ROLE_UUID_1","ROLE_UUID_2"]}'
```

To remove one role:

```bash
curl -X DELETE http://localhost:8000/api/admin/users/$USER_ID/roles/$ROLE_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Create Custom Roles

In the UI:

1. Open `/admin/roles`.
2. Create a role with a clear name and description.
3. Open the permissions action for the new role.
4. Add existing permissions or create new permissions with `resource`, `action`, and `scope`.
5. Assign the role to users from `/admin/users`.

API equivalent:

```bash
curl -X POST http://localhost:8000/api/admin/roles \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"analyst","description":"Can read owned news data","is_system":false}'
```

Create and attach a permission to that role:

```bash
curl -X POST http://localhost:8000/api/admin/roles/$ROLE_ID/permissions \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resource":"article","action":"read","scope":"own","description":"Read owned articles"}'
```

Attach an existing permission:

```bash
curl -X POST http://localhost:8000/api/admin/roles/$ROLE_ID/permissions/assign \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"permission_id":"PERMISSION_UUID"}'
```

Use `own` for normal users, `any` for cross-tenant operators, and `*` only for trusted broad-access roles. The `admin` role is special: it can use `/admin/*` and bypasses app permission checks.

## Read The Audit Log

There is no user-facing audit-log page or `/admin/audit-log` endpoint in the current application. The available auth audit trail is the `issued_refresh_token` table:

| Column | Meaning |
| --- | --- |
| `jti` | Token identifier. |
| `user_id` | User that received the refresh token. |
| `status` | `1` active, `2` rotated during refresh, `3` revoked during logout. |
| `issued_at` | When the refresh token was issued. |
| `expires_at` | When it expires. |
| `terminal_at` | When it was rotated or revoked. |
| `replaced_by_jti` | Replacement token ID after refresh rotation. |

Example database query:

```sql
SELECT
  t.user_id,
  u.email,
  t.jti,
  t.status,
  t.issued_at,
  t.expires_at,
  t.terminal_at,
  t.replaced_by_jti
FROM issued_refresh_token AS t
JOIN users AS u ON u.id = t.user_id
ORDER BY t.issued_at DESC
LIMIT 100;
```

For operational investigations, look for repeated refresh failures, unexpected revoked tokens, or token reuse attempts. Reuse attempts are rejected when a refresh token is no longer `ACTIVE`.
