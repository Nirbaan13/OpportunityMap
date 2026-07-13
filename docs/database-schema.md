# Database Schema

> Phase 1 — initial schema for OpportunityMap. See also [profile-api.md](profile-api.md) (Phase 3), [opportunities-api.md](opportunities-api.md) (Phase 4), and [matching-api.md](matching-api.md) (Phase 6).

## Overview

```mermaid
erDiagram
    users ||--o| profiles : has
    profiles }o--o{ fields : "interested in"
    opportunities }o--o{ fields : "good for"
    users ||--o{ bookmarks : saves
    opportunities ||--o{ bookmarks : saved_by
    users ||--o{ notifications : receives
    opportunities ||--o{ notifications : about

    users {
        int id PK
        string email UK
        string password_hash
        bool is_active
    }

    profiles {
        int id PK
        int user_id FK UK
        string full_name
        string location
        int grade_level
        string country_code
        enum research_experience
        enum olympiad_experience
    }

    fields {
        int id PK
        string name UK
        string slug UK
    }

    opportunities {
        int id PK
        string title
        enum opportunity_type
        string source_name
        string source_url
        datetime deadline_at
        int grade_min
        int grade_max
        array eligible_countries
    }

    bookmarks {
        int id PK
        int user_id FK
        int opportunity_id FK
    }

    notifications {
        int id PK
        int user_id FK
        int opportunity_id FK
        enum notification_type
        string title
        string message
        bool is_read
    }
```

## Tables

### `users`
Login accounts. One user has at most one profile.

| Column | Type | Notes |
|--------|------|-------|
| `email` | string | Unique, used for login (Phase 2) |
| `password_hash` | string | Bcrypt hash (Phase 2) |
| `is_active` | bool | Soft-disable accounts |

### `profiles`
Student data used for matching. Collected via the profile form (Phase 3).

| Column | Type | Notes |
|--------|------|-------|
| `full_name` | string | Student's name |
| `location` | string | City/region, e.g. `Mumbai, India` |
| `grade_level` | int | e.g. 9, 10, 11, 12 |
| `country_code` | string(2) | ISO code for eligibility, e.g. `IN`, `US` |
| `research_experience` | text | Optional — student explains research background |
| `olympiad_experience` | text | Optional — student explains olympiad background |

**Student form mapping:**

| Form field | Stored in |
|------------|-----------|
| Name | `profiles.full_name` |
| Email | `users.email` |
| Location | `profiles.location` |
| Grade | `profiles.grade_level` |
| Country | `profiles.country_code` |
| Interests (multi-select) | `profile_fields` → `fields` |
| Research experience | `profiles.research_experience` (text box) |
| Olympiad experience | `profiles.olympiad_experience` (text box) |
| Completed activities (checkboxes) | `profile_activities` → `activities` |

### `activities`
Types of activities a student can mark as done (shown on their profile).

Pre-seeded: Olympiad (national rounds of olympiads like IOI, IMO, IPhO, etc), Hackathon, Research Program, Summer School, Science Fair, Volunteering.

### `profile_activities`
Many-to-many: which activities the student has completed.

### `fields`
Shared list of topics (student interests **and** opportunity tags).

Pre-seeded: AI, Biology, Business, Chemistry, Computer Science, Economics, Engineering, Mathematics, Physics, Research, Social Science, Writing.

Matching works by finding opportunities whose `fields` overlap with the student's `profile_fields`.

### `profile_fields`
Many-to-many: which fields a student is interested in.

### `opportunities`
Programs scraped from external sites.

| Column | Type | Notes |
|--------|------|-------|
| `opportunity_type` | enum | olympiad, hackathon, research_program, summer_school, competition, scholarship, fellowship |
| `source_name` | string | Site identifier, e.g. `imo`, `regeneron` |
| `source_url` | string | Page where we found it |
| `application_url` | string | Where to apply |
| `external_id` | string | ID from source site (dedup with `source_name`) |
| `deadline_at` | datetime | Application deadline |
| `grade_eligibility` | text | Human-readable, e.g. `Grades 9-12` (from website) |
| `grade_min` / `grade_max` | int | Parsed grades for automatic matching |
| `eligible_countries` | string[] | ISO codes; `null` = all countries |
| `experience_requirements` | text | Free text from website about required experience |
| `is_active` | bool | `false` when listing is removed/stale |

### `opportunity_fields`
Many-to-many: which fields an opportunity is good for.

### `bookmarks`
Saved opportunities per user (Phase 9). `remind_me` (Phase 10) opts into 10-day and 1-day deadline alerts.

### `notifications`
Website inbox alerts (Phase 10).

| `notification_type` | When |
|---------------------|------|
| `new_match` | Reserved for future “new match” alerts |
| `deadline_reminder` | Deadline approaching (`reminder_lead_days`: 90, 30, 10, or 1) |

**Audience:** 90 / 30 days → interest overlap; 10 / 1 day → `bookmarks.remind_me`.

## Matching logic (Phase 6)

Implemented — see [matching-api.md](matching-api.md).

1. **Eligibility filter:** grade in range, country in `eligible_countries`.
2. **Interest overlap:** at least one shared `field` between profile and opportunity.
3. **Score:** shared fields + experience/activity boosts.
4. **Notify:** Phase 10 deadline reminders (see [notifications-api.md](notifications-api.md)).

## Apply migration

From `backend/` with PostgreSQL running:

```powershell
docker compose up -d          # from project root
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```
