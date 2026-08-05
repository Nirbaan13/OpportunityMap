# Field expand catalog (non-Devpost)

Curated seed of **600** high-school opportunities (`source_name=field_expand_catalog`).

- Not from Devpost
- **50 per field** across all 12 default interest fields: AI, biology, business, chemistry, computer science, economics, engineering, mathematics, physics, research, social science, writing
- Every row sets `eligible_countries` and a 2026 `deadline_at`

## Run

```bash
cd scraper
python -m scraper.main --source field_expand_catalog --skip-enrichment
```

Included in `--source all`.
