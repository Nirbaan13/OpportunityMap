# Architecture

> This document is updated as features are built. Currently at Phase 10b (freemium paywall).

See [database-schema.md](database-schema.md) for full table definitions and ER diagram.

## System Overview

OpportunityMap is a monorepo with three independent services:

| Service | Role | Deployment |
|---------|------|------------|
| Frontend | User-facing web app | Vercel |
| Backend | REST API, business logic | Railway / Render |
| Scraper | Collects opportunities from external sites | Cron job / GitHub Actions |

All services share a PostgreSQL database.

## Data Flow

1. **Scraper** periodically fetches opportunity listings from external websites.
2. **Scraper** writes parsed data to the `opportunities` table in PostgreSQL.
3. **Backend** reads opportunities and user profiles, runs the matching engine.
4. **Frontend** calls the backend API to display matched opportunities to users.

## Authentication Flow

Implemented in Phase 2.

1. User registers with `POST /api/v1/auth/register` (email + password).
2. User logs in with `POST /api/v1/auth/login` → receives JWT `access_token`.
3. Frontend sends `Authorization: Bearer <token>` on protected requests.
4. `GET /api/v1/auth/me` returns the current user.

## Opportunity browsing

Implemented in Phase 4. See [opportunities-api.md](opportunities-api.md).

1. Frontend calls `GET /api/v1/opportunities` with optional search/filter query params.
2. Backend reads from the `opportunities` table (populated by scrapers).
3. Filters include type, field, source, grade, country, deadline window, and text search.
4. No login required for browsing. Personalized ranking is available at `GET /api/v1/matches` (Phase 6).

## Frontend opportunity feed

Implemented in Phase 8. See [frontend-opportunity-feed.md](frontend-opportunity-feed.md).

1. `/opportunities` lists opportunities with search and filters.
2. Logged-in students with a profile can switch to **For you** (match scores).
3. `/opportunities/[id]` shows full detail and source/application links.

## Bookmarks

Implemented in Phase 9. See [bookmarks-api.md](bookmarks-api.md) and [frontend-bookmarks.md](frontend-bookmarks.md).

1. Logged-in students save an opportunity with `POST /api/v1/bookmarks`.
2. `GET /api/v1/bookmarks` returns saved items (newest first); `DELETE` removes by opportunity id.
3. Frontend: Save on feed/detail rows; `/bookmarks` lists them; header **Saved** when logged in.

## Deadline notifications

Implemented in Phase 10. See [notifications-api.md](notifications-api.md).

1. Daily job creates in-site `deadline_reminder` rows at 90, 30, 10, and 1 day before `deadline_at`.
2. **90 / 30 days:** students with overlapping interests (+ grade/country eligibility).
3. **10 / 1 day:** only bookmarks with `remind_me=true`.
4. Each new reminder is also emailed to the user's registered address when SMTP is set.
5. Students can also read alerts on `/notifications`.

## Freemium

Implemented before deployment. See [premium.md](premium.md).

1. Opportunity browse remains free (no login required).
2. Profile, matches, bookmarks, Remind me, and notifications require `users.is_premium`.
3. Yearly unlock via Razorpay (`PREMIUM_PRICE_INR`, default ₹299/year; `premium_until` +365 days).

## Frontend auth & profile

Implemented in Phase 7. See [frontend-auth-profile.md](frontend-auth-profile.md).

1. Landing page links to register / login.
2. JWT stored in the browser; `AuthProvider` keeps the current user in sync.
3. `/profile` creates or updates grade, country, interests, experience, and completed activities.

## Matching Algorithm

Implemented in Phase 6. See [matching-api.md](matching-api.md).

1. Load the student's profile (grade, country, interests, experience, completed activities).
2. Keep only active opportunities that pass hard eligibility (grade + country).
3. Require at least one shared interest field.
4. Score by shared fields, then boost for research/olympiad experience text and matching completed activities.
5. Return sorted matches via `GET /api/v1/matches` (JWT required).

Personalized notifications for new matches remain optional future work; deadline reminders are Phase 10.

## Scraper Schedule

- **competition_sciences** — `scraper/scraper/sources/competition_sciences.py`
- Default filter: high school competitions
- Run manually or on a schedule (daily recommended for deadline accuracy)
- See [scraper-competition-sciences.md](scraper-competition-sciences.md)
