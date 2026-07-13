# Competition Sciences Scraper

> Phase 5 — first data source: [competitionsciences.org](https://www.competitionsciences.org/competitions/?ages=high_school)

## What it scrapes

- High school competitions from the ICS archive
- **Detail page visit for every competition** (deadlines are not on the listing page)
- Stores `deadline_at` from **Registration Closes** (primary signal for notifications)
- Also saves a `Deadlines:` summary in the description (Registration Opens/Closes lines)

## Run locally

```powershell
cd scraper
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[postgres]"
playwright install chromium
copy .env.example .env

# Test run: first 2 listing pages (~18 competitions)
python -m scraper.main --max-pages 2

# Full scrape: all listing pages (slow, ~6–10 minutes)
python -m scraper.main --max-pages 0
```

Requires PostgreSQL running and migrations applied (`alembic upgrade head` from `backend/`).

## Deadline priority (for notifications)

1. Registration Closes
2. Application / Submission deadline
3. Other lines containing "deadline" or "closes"

If registration has already ended, `deadline_at` may be empty — logged as `no_deadline`.

## Field mapping

ICS categories (Biology, Mathematics, STEM, etc.) are mapped to OpportunityMap `fields` where possible. Unmapped categories are skipped.

## Source identifier

- `source_name`: `competition_sciences`
- `external_id`: URL slug (e.g. `2025-26-mtfc`)

Re-running the scraper updates existing rows and refreshes `deadline_at`.
