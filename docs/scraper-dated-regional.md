# Dated regional catalog (non-Devpost)

Curated seed of **500** high-school opportunities (`source_name=dated_regional_catalog`).

- Not from Devpost
- Every row sets `eligible_countries` explicitly (`[]` = worldwide)
- Every row sets a concrete `deadline_at` for the 2026 cycle
- Buckets: US state science fairs, national olympiads (70 countries × 4 subjects), summer/research programs, scholarships, writing, robotics, and business contests

## Run

```bash
cd scraper
python -m scraper.main --source dated_regional_catalog --skip-enrichment
```

Included in `--source all` (scheduled GitHub Action).
