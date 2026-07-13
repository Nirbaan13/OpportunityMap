# Bookmarks API

> Phase 9 — save opportunities for later. JWT required.

Uses the existing `bookmarks` table (`user_id` + `opportunity_id`, unique per pair). Phase 10 adds `remind_me` for close deadline alerts.

## List my bookmarks

`GET /api/v1/bookmarks`

Header: `Authorization: Bearer <token>`

### Query parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | `1` | Page number (1-based) |
| `page_size` | int | `20` | Page size (max 100) |

Newest bookmarks first.

### Example response `200`

```json
{
  "items": [
    {
      "opportunity": {
        "id": 1,
        "title": "International Mathematical Olympiad (IMO)",
        "opportunity_type": "olympiad",
        "source_name": "global_competitions",
        "source_url": "https://example.com",
        "application_url": null,
        "deadline_at": "2026-07-15T00:00:00Z",
        "grade_eligibility": "High school",
        "grade_min": 9,
        "grade_max": 12,
        "eligible_countries": null,
        "is_active": true,
        "fields": [{ "id": 1, "name": "Mathematics", "slug": "mathematics" }]
      },
      "remind_me": false,
      "created_at": "2026-07-11T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

## Save an opportunity

`POST /api/v1/bookmarks`

Header: `Authorization: Bearer <token>`

### Body

```json
{
  "opportunity_id": 1,
  "remind_me": false
}
```

`remind_me` is optional (default `false`).

### Responses

| Status | Meaning |
|--------|---------|
| `201` | Created — returns `BookmarkItem` |
| `404` | Opportunity does not exist |
| `409` | Already bookmarked |
| `401` | Missing/invalid token |

## Check one bookmark

`GET /api/v1/bookmarks/{opportunity_id}`

Header: `Authorization: Bearer <token>`

| Status | Meaning |
|--------|---------|
| `200` | Bookmarked — returns `BookmarkItem` (includes `remind_me`) |
| `404` | Not bookmarked (or opportunity id unused by this user) |
| `401` | Missing/invalid token |

## Set Remind me

`PATCH /api/v1/bookmarks/{opportunity_id}`

Header: `Authorization: Bearer <token>`

```json
{
  "remind_me": true
}
```

Creates a bookmark if turning Remind me **on** and none exists. Opt-in for **10-day** and **1-day** website deadline alerts (see [notifications-api.md](notifications-api.md)).

## Remove a bookmark

`DELETE /api/v1/bookmarks/{opportunity_id}`

Header: `Authorization: Bearer <token>`

| Status | Meaning |
|--------|---------|
| `204` | Removed |
| `404` | Bookmark not found |
| `401` | Missing/invalid token |

Deleting uses `opportunity_id` (not the bookmark row id) so clients can toggle from feed/detail without an extra lookup.
