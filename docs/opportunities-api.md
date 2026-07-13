# Opportunities API

> Phase 4 — list, search, and filter scraped opportunities.

No login required for browsing. For a personalized ranked feed, use [matching-api.md](matching-api.md).

## List / search / filter

`GET /api/v1/opportunities`

### Query parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | — | Case-insensitive search in title and description |
| `opportunity_type` | enum | — | `olympiad`, `hackathon`, `research_program`, `summer_school`, `competition`, `scholarship`, `fellowship` |
| `field` | string | — | Interest field slug (`mathematics`, `ai`, …). See `GET /api/v1/fields`. |
| `source` | string | — | Scraper source (`devpost`, `global_competitions`, `pathways_to_science`, …) |
| `country` | string(2) | — | ISO country code. Keeps worldwide listings (`eligible_countries` null) and those that include the code. |
| `grade` | int 6–12 | — | Keeps listings with no grade bounds or whose `grade_min`/`grade_max` include this grade. |
| `deadline_before` | datetime | — | Deadline on or before this time (ISO 8601) |
| `deadline_after` | datetime | — | Deadline on or after this time |
| `open_only` | bool | `false` | Only listings with a deadline still in the future |
| `active` | bool | `true` | Hide stale (`is_active=false`) listings |
| `sort` | enum | `deadline_asc` | `deadline_asc`, `deadline_desc`, `newest`, `title` |
| `page` | int | `1` | Page number (1-based) |
| `page_size` | int | `20` | Page size (max 100) |

### Example

```
GET /api/v1/opportunities?q=math&opportunity_type=olympiad&grade=11&country=IN&open_only=true&sort=deadline_asc&page=1&page_size=20
```

### Response `200`

```json
{
  "items": [
    {
      "id": 1,
      "title": "International Mathematical Olympiad",
      "opportunity_type": "olympiad",
      "source_name": "global_competitions",
      "source_url": "https://example.com",
      "application_url": "https://example.com/apply",
      "deadline_at": "2026-09-01T00:00:00Z",
      "grade_eligibility": "Grades 9-12",
      "grade_min": 9,
      "grade_max": 12,
      "eligible_countries": null,
      "is_active": true,
      "fields": [
        { "id": 8, "name": "Mathematics", "slug": "mathematics" }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

`eligible_countries: null` means open to all countries.

Sort `deadline_asc` puts null deadlines last so students see actionable deadlines first.

## Get one opportunity

`GET /api/v1/opportunities/{id}`

Returns the same fields as a list item, plus:

- `description`
- `experience_requirements`
- `external_id`
- `last_scraped_at`
- `created_at`
- `updated_at`

### Errors

| Status | When |
|--------|------|
| 404 | Opportunity id does not exist |
| 422 | Invalid query param (bad enum, grade out of range, etc.) |

## Notes for frontend (Phase 8)

1. Call `GET /api/v1/fields` to populate the field filter chips.
2. Use `opportunity_type` for type tabs/filters.
3. Pass the student's `grade` and `country` from their profile when available — this is a hard filter, not the match score.
4. Prefer `open_only=true` on the default feed so expired deadlines stay out of the list.
5. For ranked recommendations, call `GET /api/v1/matches` instead (requires login + profile).
