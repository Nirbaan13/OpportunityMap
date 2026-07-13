# Pathways to Science — high-school research internships (not competitions)

Source: [pathwaystoscience.org](https://www.pathwaystoscience.org/programs.aspx)

For **hackathons/competitions**, use `--source devpost` or `--source global_competitions`.

## What we scrape

- **Listing:** Advanced search filtered to `HighSchool` academic level
- **Detail pages:** `programhub.aspx?sort=...`
- **Fields parsed:** title, description, academic level, application deadline, disciplines, application URL
- **Stored as:** `source_name = pathways_to_science`, `external_id = sort` query parameter

## Run locally

```bash
# From repo root — start Postgres
docker compose up -d

# Backend migrations
cd backend
alembic upgrade head

# Scraper
cd ../scraper
.\.venv\Scripts\activate
pip install -e ".[postgres]"
python -m scraper.main --source pathways_to_science --max-items 20
```

## CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--source pathways_to_science` | (default) | Use this scraper |
| `--max-items 20` | 20 | Limit programs scraped (0 = all on listing page) |
| `--delay 1.0` | 1.0 | Seconds between HTTP requests |

## Notes

- The high-school search returns up to 25 programs per query; pagination is limited on the site.
- The high-school search still lists some grad/postdoc programs; we skip anything that is not clearly high-school level.
- Deadlines may be rolling or multi-cycle; programs without a parseable deadline or with a past deadline are skipped.

## Global competitions seed

For international olympiads and science fairs (no live scraping), use:

```bash
python -m scraper.main --source global_competitions
```

This upserts curated entries (IMO, IOI, IPhO, IChO, IBO, ISEF, etc.) with `source_name = global_competitions`.
