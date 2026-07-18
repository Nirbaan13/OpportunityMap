"""OpportunityMap scraper entry point."""

from __future__ import annotations

import argparse
import logging

import scraper.db  # noqa: F401 — adds backend/ to sys.path for SQLAlchemy models

from scraper.curl_client import CurlClient
from scraper.db import SessionLocal
from scraper.http_client import BrowserClient
from scraper.maintenance import deactivate_past_deadlines
from scraper.sources.competition_sciences import scrape_competition_sciences
from scraper.sources.devpost import scrape_devpost
from scraper.sources.field_coverage_catalog import seed_field_coverage_catalog
from scraper.sources.global_competitions import seed_global_competitions
from scraper.sources.pathways_to_science import scrape_pathways_to_science

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

SOURCES = (
    "devpost",
    "pathways_to_science",
    "global_competitions",
    "field_coverage_catalog",
    "competition_sciences",
    "all",
)


def _run_source(
    db,
    source: str,
    *,
    max_pages: int,
    max_items: int,
    delay: float,
    headed: bool,
) -> dict[str, int]:
    if source == "competition_sciences":
        with BrowserClient(headed=headed) as client:
            return scrape_competition_sciences(
                db,
                client,
                max_pages=max_pages,
                delay_seconds=delay,
            )
    if source == "devpost":
        with CurlClient(delay_seconds=delay) as client:
            return scrape_devpost(
                db,
                client,
                max_items=max_items,
                max_pages=max_pages if max_pages > 0 else 5,
                delay_seconds=delay,
            )
    if source == "pathways_to_science":
        with CurlClient(delay_seconds=delay) as client:
            return scrape_pathways_to_science(
                db,
                client,
                max_items=max_items,
                delay_seconds=delay,
            )
    if source == "field_coverage_catalog":
        return seed_field_coverage_catalog(db)
    if source == "global_competitions":
        return seed_global_competitions(db)
    raise ValueError(f"Unknown source: {source}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OpportunityMap scrapers")
    parser.add_argument(
        "--source",
        default="all",
        choices=SOURCES,
        help="Which source to scrape (default: all automated sources)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Listing pages for competition_sciences or devpost (0 = all pages)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=80,
        help="Max items for live scrapers (0 = all on listing page)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between requests",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Show the browser window (competition_sciences only)",
    )
    parser.add_argument(
        "--skip-maintenance",
        action="store_true",
        help="Skip deactivating past-deadline opportunities",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        sources = (
            [
                "global_competitions",
                "field_coverage_catalog",
                "pathways_to_science",
                "devpost",
            ]
            if args.source == "all"
            else [args.source]
        )
        for source in sources:
            print(f"\n=== {source} ===")
            stats = _run_source(
                db,
                source,
                max_pages=args.max_pages,
                max_items=args.max_items,
                delay=args.delay,
                headed=args.headed,
            )
            print("Scrape finished:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        if not args.skip_maintenance:
            deactivated = deactivate_past_deadlines(db)
            print(f"\nMaintenance: deactivated {deactivated} past-deadline opportunit(ies)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
