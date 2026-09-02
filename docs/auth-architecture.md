# Auth Architecture

The backend uses FastAPI dependencies, JWT access tokens, rotating refresh tokens, role-based access control, and row ownership through `owner_id`.

## Token Flow

```mermaid
sequenceDiagram
    participant Browser
    participant API as FastAPI /api
    participant DB as PostgreSQL

    Browser->>API: POST /auth/login (email, password)
    API->>DB: Load active user with roles and permissions
    API->>DB: Insert issued_refresh_token(status=ACTIVE)
    API-->>Browser: access_token + refresh_token

    Browser->>API: API request with Authorization: Bearer access_token
    API->>API: Decode JWT and load current user
    API->>DB: Load roles and permissions for AuthorizationContext
    API-->>Browser: Protected response

    Browser->>API: Request after access token expires
    API-->>Browser: 401
    Browser->>API: POST /auth/refresh (refresh_token)
    API->>DB: Verify refresh jti is ACTIVE
    API->>DB: Mark old jti ROTATED and insert replacement ACTIVE jti
    API-->>Browser: New access_token + new refresh_token
    Browser->>API: Retry original request with new access_token

    Browser->>API: POST /auth/logout (refresh_token)
    API->>DB: Mark refresh jti REVOKED
    API-->>Browser: Logged out
```

Login accepts `application/x-www-form-urlencoded` credentials through `OAuth2PasswordRequestForm`; the username field is the user's email. Access tokens contain `sub`, `user_id`, `roles`, `permissions`, `type=access`, `jti`, `exp`, `iat`, and `iss`. Refresh tokens contain identity and token metadata, but not roles or permissions.

The frontend keeps the refresh token in `localStorage`, keeps the access token in Pinia state, attaches the access token in the Axios request interceptor, and performs single-flight refresh on `401`. Single-flight refresh is important because the backend rotates refresh tokens and rejects reuse.

## Refresh-On-401

`frontend/src/lib/axios.ts` owns automatic recovery:

1. Protected requests use `api`, which adds `Authorization: Bearer <access_token>`.
2. If a non-auth endpoint returns `401`, the client calls `/auth/refresh` once and shares that promise across concurrent requests.
3. The original request is retried with the new access token.
4. If refresh fails, an auth endpoint returns `401`, or the retried request returns `401`, the frontend clears the session and redirects to `/login`.

## Logout

Logout posts the refresh token to `/auth/logout`. The backend validates that the token is active and marks its `issued_refresh_token.status` as `REVOKED`. The frontend clears local auth/admin/app stores in a `finally` block, so local logout still happens if the server call fails.

## Request Lifecycle

```mermaid
flowchart TD
    A[Incoming protected request] --> B[OAuth2 bearer token dependency]
    B -->|missing/invalid/expired| Z1[401 Unauthorized]
    B --> C[get_current_user]
    C --> D[Load User by JWT sub]
    D -->|not found| Z1
    D --> E[get_current_active_user]
    E -->|inactive| Z1
    E --> F[get_authorization_context]
    F --> G[Load user roles and role permissions]
    G --> H[RequiredPermissionsAndOwnership]
    H -->|admin role| OK[PermissionGranted is_any=true]
    H --> I{Has required permission?}
    I -->|no| Z2[403 Forbidden]
    I -->|yes| J{resource_type and PUT/PATCH/DELETE?}
    J -->|no| OK
    J -->|yes| K[Read resource_id path param]
    K --> L[Ownership resolver loads resource]
    L -->|missing| Z3[404 Not Found]
    L --> M{owner_id matches current user?}
    M -->|no| Z2
    M -->|yes| OK
    OK --> N[Repository/service]
    N --> O{PermissionGranted.is_any?}
    O -->|false| P[Apply owner_id filter]
    O -->|true| Q[Skip owner_id filter]
    P --> R[Response]
    Q --> R
```

## Ownership Model

Owned tables inherit `OwnerMixin` and have a non-null `owner_id` FK to `users.id`. Current owned resources include:

- `sources`
- `crawl_jobs`
- `monitored_keywords`
- `outbox_events`
- `articles`
- `keyword_hits`

Reads are scoped in repositories/services with `filter_owned_resources()`: callers with `:own` permissions see only rows where `owner_id == current_user.id`; callers with an `:any` permission or the `admin` role see all rows. Mutating routes that pass a `resource_type` also perform an ownership check against `{resource_id}` for `PUT`, `PATCH`, and `DELETE`.

Admins bypass both permission matching and ownership checks because `RequiredPermissionsAndOwnership` returns `PermissionGranted(is_any=True)` whenever the caller has the `admin` role. Admin-only management routes use `RequiredRoles("admin")`, so custom roles cannot access `/admin/*` unless they are named `admin`.
