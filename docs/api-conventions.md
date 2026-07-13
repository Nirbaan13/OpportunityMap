# API Conventions

> This document is updated as endpoints are added. Currently at Phase 10.

## Base URL

- Local: `http://localhost:8000`
- Production: TBD (Railway / Render)

## Versioning

All endpoints are prefixed with `/api/v1/`.

Example: `GET /api/v1/health`

## Request Format

- Content-Type: `application/json` for POST/PUT/PATCH bodies.
- Authentication header (Phase 2+): `Authorization: Bearer <token>`

## Response Format

### Success

Return the resource directly or wrapped in a consistent shape:

```json
{
  "status": "ok"
}
```

### Error

FastAPI default error format:

```json
{
  "detail": "Human-readable error message"
}
```

Validation errors return HTTP 422 with:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No content (delete) |
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 422 | Validation error |
| 500 | Server error |

## Naming Conventions

- URLs use kebab-case: `/api/v1/opportunity-types`
- JSON fields use snake_case: `deadline_date`, `grade_level`
- Plural nouns for collections: `/api/v1/opportunities`
- Singular for actions: `/api/v1/auth/login`

## Pagination

List endpoints that can return many rows use page-based pagination:

```json
{
  "items": [],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

Query params: `page` (1-based, default 1) and `page_size` (default 20, max 100).

## Endpoint docs

| Area | Doc |
|------|-----|
| Auth | [authentication.md](authentication.md) |
| Profiles | [profile-api.md](profile-api.md) |
| Opportunities | [opportunities-api.md](opportunities-api.md) |
| Matching | [matching-api.md](matching-api.md) |
| Bookmarks | [bookmarks-api.md](bookmarks-api.md) |
| Notifications | [notifications-api.md](notifications-api.md) |
| Premium | [premium.md](premium.md) |
| Frontend auth/profile | [frontend-auth-profile.md](frontend-auth-profile.md) |
| Frontend opportunity feed | [frontend-opportunity-feed.md](frontend-opportunity-feed.md) |
| Frontend bookmarks | [frontend-bookmarks.md](frontend-bookmarks.md) |
| Frontend notifications | [frontend-notifications.md](frontend-notifications.md) |
