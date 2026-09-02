# Permission Matrix

Permissions use the shape `resource:action:scope`.

- `own`: grants the action only for rows owned by the current user.
- `any`: grants the action across all owners. Repositories receive `PermissionGranted.is_any=True` and skip `owner_id` filters.
- `*`: wildcard scope accepted by the RBAC matcher and admin UI. Use it sparingly for broad operational roles.
- `*:*:*` is also supported by the matcher, but should be reserved for trusted system roles if introduced.

The hard-coded `admin` role bypasses permission checks in `RequiredPermissionsAndOwnership`, even if the role has no permission rows.

## Permissions

| Permission | Grants |
| --- | --- |
| `source:create:own` | Create sources owned by the current user. |
| `source:create:any` | Create sources while carrying a broad source-create grant. Created rows are still assigned to the acting user by current repository code. |
| `source:create:*` | Wildcard source creation grant. |
| `source:read:own` | List and read only sources whose `owner_id` is the current user. |
| `source:read:any` | List and read sources for all owners. |
| `source:read:*` | Wildcard source read grant. |
| `source:update:own` | Reserved by the catalog for updating owned sources. No source update endpoint currently consumes it. |
| `source:update:any` | Reserved by the catalog for updating any source. No source update endpoint currently consumes it. |
| `source:update:*` | Wildcard source update grant. No source update endpoint currently consumes it. |
| `source:delete:own` | Reserved by the catalog for deleting owned sources. No source delete endpoint currently consumes it. |
| `source:delete:any` | Reserved by the catalog for deleting any source. No source delete endpoint currently consumes it. |
| `source:delete:*` | Wildcard source delete grant. No source delete endpoint currently consumes it. |
| `source:run:own` | Manually dispatch an owned source crawl with `POST /sources/{resource_id}/run`. |
| `source:run:any` | Manually dispatch crawls for sources owned by any user. |
| `source:run:*` | Wildcard source run grant. |
| `article:read:own` | Read/search articles owned by the current user. |
| `article:read:any` | Read/search articles for all owners. |
| `article:read:*` | Wildcard article read grant. |
| `keyword:create:own` | Create monitored keywords owned by the current user. |
| `keyword:create:any` | Create monitored keywords while carrying a broad keyword-create grant. Created rows are still assigned to the acting user by current repository code. |
| `keyword:create:*` | Wildcard keyword create grant. |
| `keyword:read:own` | List and read monitored keywords owned by the current user. |
| `keyword:read:any` | List and read monitored keywords for all owners. |
| `keyword:read:*` | Wildcard keyword read grant. |
| `keyword:update:own` | Update monitored keywords owned by the current user. |
| `keyword:update:any` | Update monitored keywords owned by any user. |
| `keyword:update:*` | Wildcard keyword update grant. |
| `keyword:delete:own` | Reserved by the catalog for deleting owned keywords. No keyword delete endpoint currently consumes it. |
| `keyword:delete:any` | Reserved by the catalog for deleting any keyword. No keyword delete endpoint currently consumes it. |
| `keyword:delete:*` | Wildcard keyword delete grant. No keyword delete endpoint currently consumes it. |
| `alert:read:own` | Connect to owned alert stream events through `/ws/alerts`. |
| `alert:read:any` | Connect to alert stream events across owners. |
| `alert:read:*` | Wildcard alert read grant. |
| `job:read:own` | Read crawl jobs owned by the current user. |
| `job:read:any` | Read crawl jobs for all owners. |
| `job:read:*` | Wildcard job read grant. |
| `dashboard:read:own` | Read dashboard stats scoped to the current user. |
| `dashboard:read:any` | Read dashboard stats across all owners. |
| `dashboard:read:*` | Wildcard dashboard read grant. |

## Default Roles

| Role | Seeded by | Default permissions | Notes |
| --- | --- | --- | --- |
| `admin` | Migration `20260728_2253_add_auth_models.py` and `app/db/seed_data.py` | None required | Bypasses `RequiredPermissionsAndOwnership`; required for `/admin/*` routes via `RequiredRoles("admin")`. |
| `manager` | `app/db/seed_data.py` | None | System role placeholder. Grant permissions explicitly before use. |
| `user` | Migration `20260728_2253_add_auth_models.py` and `app/db/seed_data.py` | None | Regular role placeholder. Grant permissions explicitly before use. |

New registrations do not receive a role automatically in the current code. Admins should assign roles after creating or approving users.
