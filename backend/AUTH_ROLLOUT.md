# Auth rollout runbook

## Environment variables
- `JWT_SECRET`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `AUTH_RATE_LIMIT_PER_MINUTE`

## Migration and seed
1. Run Alembic migration to `head`.
2. Login using seeded admin account:
   - email: `admin@news-crawler.local`
   - password: `ChangeMe123!`
3. Rotate admin password immediately using admin user update API.

## Frontend integration checklist
- Add login form and call `POST /api/auth/login`.
- Persist `access_token` and `refresh_token` securely.
- Add token refresh flow via `POST /api/auth/refresh`.
- Add logout flow via `POST /api/auth/logout`.
- Add `Authorization: Bearer <access_token>` to protected requests.
- Build admin user/role management screens for `/api/admin/*`.
- Handle `401/403/429` responses globally and redirect/notify users.

## Validation commands
- Backend: `cd /home/runner/work/news_crawler/news_crawler/backend && python -m pytest`
- Frontend: `cd /home/runner/work/news_crawler/news_crawler/frontend && npm run build`
