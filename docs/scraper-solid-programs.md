# Solid programs catalog (non-Devpost)

Curated seed of **100** real high-school opportunities (`source_name=solid_programs_catalog`).

- Not from Devpost
- Every row sets `eligible_countries` explicitly (`[]` = worldwide)
- Almost all rows also set a concrete `deadline_at` for the 2026 cycle

## Run

```bash
cd scraper
python -m scraper.main --source solid_programs_catalog --skip-enrichment
```

Included in `--source all` (weekly GitHub Action).
