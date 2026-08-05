# Core STEM + business/economics catalog (non-Devpost)

Curated seed of **240** high-school opportunities (`source_name=core_stem_business_catalog`).

- Not from Devpost
- **40 each** in mathematics, physics, chemistry, biology, business, economics
- Every row sets `eligible_countries` (`[]` = worldwide) and a 2026 `deadline_at`

## Run

```bash
cd scraper
python -m scraper.main --source core_stem_business_catalog --skip-enrichment
```

Included in `--source all`.
