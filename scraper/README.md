# OpportunityMap Scraper

Collects opportunity listings from external websites and writes them to the database.

## Prerequisites

- Python 3.12+
- PostgreSQL running locally (see root `docker-compose.yml`)

## Setup

From the `scraper/` directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[postgres]"
playwright install   # only needed for competition_sciences
copy .env.example .env
```

## Run

```powershell
# Devpost — online beginner-friendly hackathons (best for competitions)
python -m scraper.main --source devpost --max-items 20

# Pathways — high-school research internships (not PhD fellowships)
python -m scraper.main --source pathways_to_science --max-items 20

# Global olympiads & science fairs — curated seed, no HTTP scraping
python -m scraper.main --source global_competitions

# Institute of Competition Sciences (often blocked — use --headed)
python -m scraper.main --source competition_sciences --max-pages 2 --headed
```

## Sources

| Source | What it collects | Method |
|--------|------------------|--------|
| `all` (default) | Runs catalogs + live scrapers together | Combined |
| `field_coverage_catalog` | Olympiads/research/competitions across **every interest field** (AI, chemistry, physics, social science, writing, business, …) | Curated seed, upserted each run |
| `global_competitions` | Flagship international olympiads & ISEF | Curated seed |
| `devpost` | Online beginner-friendly hackathons | JSON API |
| `pathways_to_science` | High-school research internships | HTTP |
| `competition_sciences` | ICS competitions | Playwright (often blocked; not in daily CI) |

## Automated updates

GitHub Actions runs **daily** (`scrape-opportunities.yml`):

1. Upserts catalog + scraped listings (same `source_name` + `external_id` → update deadlines/text)
2. Deactivates opportunities whose deadlines have passed

```powershell
python -m scraper.main --source all --max-items 80
```


## Project Structure

```
scraper/
├── main.py           # CLI entry point
├── curl_client.py    # HTTP client (curl_cffi)
├── http_client.py    # Playwright browser client
├── sources/          # One module per website
└── parsers/          # Shared HTML parsing utilities
```

## Adding a New Source

1. Create a file in `scraper/sources/` (e.g. `example_site.py`).
2. Implement a scrape function that upserts via `repository.upsert_opportunity`.
3. Register the source in `main.py`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |

## Database Strategy

Phase 1: Scraper writes directly to PostgreSQL using shared SQLAlchemy models from the backend.
