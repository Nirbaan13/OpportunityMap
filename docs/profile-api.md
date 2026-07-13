# Profile API

> Phase 3 — student profile with interests and completed activities checklist.

## Option lists (no login required)

### Interest fields

`GET /api/v1/fields`

Returns all subjects students can select as interests (AI, Physics, Business, etc.).

### Activity types

`GET /api/v1/activities`

Returns activities students can tick as completed (Olympiad, Hackathon, etc.).

## Profile endpoints (login required)

Send header: `Authorization: Bearer <token>`

### Create profile

`POST /api/v1/profiles/me`

```json
{
  "full_name": "Ada Student",
  "location": "Mumbai, India",
  "grade_level": 11,
  "country_code": "IN",
  "research_experience": "Built a ML model for plant disease detection.",
  "olympiad_experience": "Qualified for national math olympiad camp.",
  "interest_slugs": ["mathematics", "physics", "ai"],
  "completed_activity_slugs": ["olympiad", "science-fair"]
}
```

Response `201` includes `interests` and `completed_activities` as full objects so the student can see what they have done.

### Get profile

`GET /api/v1/profiles/me`

Returns the full profile including ticked activities — this is the "what I have done so far" view.

### Update profile

`PUT /api/v1/profiles/me`

Same body as create. Replaces interests and completed activities with the new lists.

## Completed activities checklist

Students tick items from `GET /api/v1/activities`:

| Activity | Slug |
|----------|------|
| Olympiad (national rounds of olympiads like IOI, IMO, IPhO, etc) | `olympiad` |
| Hackathon | `hackathon` |
| Research Program | `research-program` |
| Summer School | `summer-school` |
| Science Fair | `science-fair` |
| Volunteering | `volunteering` |

Send selected slugs in `completed_activity_slugs`. The profile response echoes them under `completed_activities`.

## Errors

| Status | When |
|--------|------|
| 400 | Invalid interest or activity slug |
| 401 | Not logged in |
| 404 | Profile does not exist (GET/PUT) |
| 409 | Profile already exists (POST) |
