# Frontend opportunity feed (Phase 8)

Browse and filter scraped opportunities, plus a personalized “For you” feed.

## Pages

| Path | Purpose |
|------|---------|
| `/opportunities` | Feed with filters; Browse all / For you modes |
| `/opportunities/[id]` | Opportunity detail + apply/source links |

## Browse all

Calls `GET /api/v1/opportunities`.

Filters:

- Search (`q`)
- Opportunity type chips
- Interest field chips (`GET /api/v1/fields`)
- Open deadlines only
- Eligible for my grade/country (when logged in with a profile)
- Sort: deadline / newest / title
- Pagination

## For you

Calls `GET /api/v1/matches` (JWT + premium + profile required).

Shows match score and reasons.

## Row actions

- **Remind me** — shown on every row (guests: log in; free: ~30-day inbox; premium: 10/1 + email)
- **Save / Mark done** — premium only (not shown as unlock spam for free users)

## Run

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\PassionProject\frontend
npm run dev
```

Open http://localhost:3000/opportunities
