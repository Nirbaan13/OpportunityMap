"""OpportunityMap scraper entry point."""

from __future__ import annotations

import argparse
import logging

import scraper.db  # noqa: F401 — adds backend/ to sys.path for SQLAlchemy models

from scraper.curl_client import CurlClient
from scraper.db import SessionLocal
from scraper.http_client import BrowserClient
from scraper.sources.competition_sciences import scrape_competition_sciences
from scraper.sources.devpost import scrape_devpost
from scraper.sources.global_competitions import seed_global_competitions
from scraper.sources.pathways_to_science import scrape_pathways_to_science

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

SOURCES = ("devpost", "pathways_to_science", "global_competitions", "competition_sciences")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OpportunityMap scrapers")
    parser.add_argument(
        "--source",
        default="devpost",
        choices=SOURCES,
        help="Which website to scrape",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Listing pages for competition_sciences or devpost (0 = all pages)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=20,
        help="Max items to scrape for devpost/pathways (0 = all on listing page)",
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
    args = parser.parse_args()

    db = SessionLocal()
    stats: dict[str, int]
    try:
        if args.source == "competition_sciences":
            with BrowserClient(headed=args.headed) as client:
                stats = scrape_competition_sciences(
                    db,
                    client,
                    max_pages=args.max_pages,
                    delay_seconds=args.delay,
                )
        elif args.source == "devpost":
            with CurlClient(delay_seconds=args.delay) as client:
                stats = scrape_devpost(
                    db,
                    client,
                    max_items=args.max_items,
                    max_pages=args.max_pages if args.max_pages > 0 else 3,
                    delay_seconds=args.delay,
                )
        elif args.source == "pathways_to_science":
            with CurlClient(delay_seconds=args.delay) as client:
                stats = scrape_pathways_to_science(
                    db,
                    client,
                    max_items=args.max_items,
                    delay_seconds=args.delay,
                )
        else:
            stats = seed_global_competitions(db)
    finally:
        db.close()

    print("Scrape finished:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
