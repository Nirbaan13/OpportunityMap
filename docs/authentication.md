# Authentication API

> Phase 2 — JWT-based registration and login.

## Endpoints

### Register

`POST /api/v1/auth/register`

```json
{
  "email": "student@example.com",
  "password": "securepass123"
}
```

Response `201`:

```json
{
  "id": 1,
  "email": "student@example.com",
  "is_active": true,
  "created_at": "2026-07-07T12:00:00Z",
  "has_profile": false
}
```

Password must be at least 8 characters.

Emails are stored **lowercase**. Login and password-reset match case-insensitively
and heal legacy mixed-case rows on successful login.

### Login

`POST /api/v1/auth/login`

```json
{
  "email": "student@example.com",
  "password": "securepass123"
}
```

Response `200`:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### Current user

`GET /api/v1/auth/me`

Header: `Authorization: Bearer <jwt>`

Response `200`: same shape as register response.

## Rate limits (per client IP, per minute)

| Endpoint | Limit |
|----------|-------|
| `POST /register` | 5 |
| `POST /login` | 10 |
| `POST /forgot-password` | 3 |
| `POST /reset-password` | 10 |
| `GET /admin/overview` | 30 |

Exceeded → `429 Too many requests`.

## Errors

| Status | When |
|--------|------|
| 401 | Wrong password, invalid token, or not logged in |
| 409 | Email already registered |
| 429 | Rate limit exceeded |

## Frontend usage (Phase 7)

1. Call login → store `access_token` in memory or `localStorage`.
2. Send token on every API request: `Authorization: Bearer <token>`.
3. Token expires after 7 days (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
