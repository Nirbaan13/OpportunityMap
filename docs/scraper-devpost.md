# Devpost scraper

Source: [devpost.com/hackathons](https://devpost.com/hackathons)

Devpost lists hackathons and coding competitions. We use the public JSON API (not the HTML filter UI).

## Filters applied

Only hackathons that match **all** of these are stored:

| Filter | Value |
|--------|-------|
| Location | Online |
| Interest tag | Beginner Friendly |
| Status | Open |
| Deadline | Must be parseable and in the future |
| Eligibility | Skips adults-only (`Ages 18+`) events |

## Run

```bash
cd scraper
.\.venv\Scripts\activate
python -m scraper.main --source devpost --max-items 20
```

## Notes

- Opportunity type is stored as `hackathon`.
- Grade eligibility defaults to high school (grades 9–12); 18+ events are skipped.
- For international olympiads, use `--source global_competitions`.
- Pathways (`--source pathways_to_science`) is for high-school research internships, not PhD fellowships.
