# Matching API

> Phase 6 — personalized opportunity feed based on the student profile.

Requires login **and** a profile with at least one interest.

## Get my matches

`GET /api/v1/matches`

Header: `Authorization: Bearer <token>`

### Query parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `open_only` | bool | `true` | Only opportunities with a future deadline |
| `opportunity_type` | enum | — | Optional type filter |
| `page` | int | `1` | Page number (1-based) |
| `page_size` | int | `20` | Page size (max 100) |

### How matching works

**1. Hard eligibility (must pass)**

- Opportunity is active
- Student's grade is within `grade_min`/`grade_max` (missing bounds = unrestricted)
- Student's country is allowed (`eligible_countries` null = worldwide)
- At least one shared interest field between profile and opportunity

**2. Soft score (higher = better fit)**

| Rule | Points |
|------|--------|
| Each shared interest field | +10 |
| Non-empty `research_experience` and type is research/summer school/fellowship/scholarship | +5 |
| Non-empty `olympiad_experience` and type is olympiad/competition | +5 |
| Completed activity maps to this opportunity type | +3 |

**3. Sort order**

1. Score (highest first)
2. Soonest deadline
3. Opportunity id

Notifications when new matches appear are Phase 10 — this endpoint only ranks what is already in the database.

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
        "deadline_at": null,
        "grade_eligibility": "High school",
        "grade_min": 9,
        "grade_max": 12,
        "eligible_countries": null,
        "is_active": true,
        "fields": [
          { "id": 8, "name": "Mathematics", "slug": "mathematics" }
        ]
      },
      "score": 18,
      "shared_fields": [
        { "id": 8, "name": "Mathematics", "slug": "mathematics" }
      ],
      "reasons": [
        "1 shared interest: Mathematics",
        "olympiad experience boost",
        "completed olympiad activity"
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid token |
| 404 | No profile yet — create one with `POST /api/v1/profiles/me` |
| 400 | Profile has no interests |
| 422 | Invalid query param |

### Tip

Use `open_only=false` if you want to include listings without a future deadline (e.g. year-round olympiads seeded without dates).
