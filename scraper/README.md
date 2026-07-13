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
| `devpost` | Online beginner-friendly hackathons | JSON API |
| `global_competitions` | International olympiads & science fairs | Curated seed |
| `pathways_to_science` | High-school research internships | HTTP |
| `competition_sciences` | ICS competitions | Playwright (often blocked) |

## CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--source` | `devpost` | Which scraper to run |
| `--max-items` | 20 | Max programs for pathways (0 = all on page) |
| `--max-pages` | 2 | Listing pages for competition_sciences |
| `--delay` | 1.0 | Seconds between requests |
| `--headed` | off | Show browser (competition_sciences only) |

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
