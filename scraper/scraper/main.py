"""OpportunityMap scraper entry point."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from typing import TypeVar

import scraper.db  # noqa: F401 — adds backend/ to sys.path for SQLAlchemy models

from scraper.curl_client import CurlClient
from scraper.db import SessionLocal
from scraper.enrich_deadlines import enrich_catalog_deadlines
from scraper.http_client import BrowserClient
from scraper.maintenance import (
    backfill_eligible_countries,
    backfill_opportunity_fields,
    deactivate_past_deadlines,
    deactivate_stale_listings,
    deactivate_unusable_titles,
)
from scraper.sources.competition_sciences import scrape_competition_sciences
from scraper.sources.devpost import scrape_devpost
from scraper.sources.expanded_catalog import seed_expanded_catalog
from scraper.sources.field_coverage_catalog import seed_field_coverage_catalog
from scraper.sources.global_competitions import seed_global_competitions
from scraper.sources.dated_regional_catalog import seed_dated_regional_catalog
from scraper.sources.mun_catalog import seed_mun_catalog
from scraper.sources.pathways_to_science import scrape_pathways_to_science
from scraper.sources.solid_programs_catalog import seed_solid_programs_catalog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

SOURCES = (
    "devpost",
    "pathways_to_science",
    "global_competitions",
    "field_coverage_catalog",
    "expanded_catalog",
    "solid_programs_catalog",
    "mun_catalog",
    "dated_regional_catalog",
    "competition_sciences",
    "all",
)

# Network / WAF flaky in CI. On `--source all`, treat these as soft-fail so curated
# catalog seeds + enrichment + maintenance (country/field backfill) still finish and
# the scheduled workflow can exit 0. Single-source runs still hard-fail.
LIVE_NETWORK_SOURCES = frozenset(
    {
        "pathways_to_science",
        "devpost",
        "competition_sciences",
    }
)

T = TypeVar("T")


def is_soft_fail_source(requested_source: str, failed_source: str) -> bool:
    """True when a live-network source failure should not fail `--source all`."""
    return requested_source == "all" and failed_source in LIVE_NETWORK_SOURCES


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
    if source == "expanded_catalog":
        return seed_expanded_catalog(db)
    if source == "solid_programs_catalog":
        return seed_solid_programs_catalog(db)
    if source == "mun_catalog":
        return seed_mun_catalog(db)
    if source == "dated_regional_catalog":
        return seed_dated_regional_catalog(db)
    if source == "global_competitions":
        return seed_global_competitions(db)
    raise ValueError(f"Unknown source: {source}")


def _run_maintenance_step(
    name: str,
    fn: Callable[[], T],
    *,
    soft: bool,
    db,
) -> T | None:
    try:
        return fn()
    except Exception:
        if soft:
            logger.exception(
                "Maintenance step %s failed (soft-fail); continuing", name
            )
            print(f"Maintenance step {name} FAILED (soft-fail); continuing.")
            try:
                db.rollback()
            except Exception:
                logger.exception("Could not rollback after %s failure", name)
            return None
        raise


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
        default=8,
        help="Listing pages for competition_sciences or devpost (0 = all pages)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=150,
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
        help="Skip deactivating past-deadline / junk-title opportunities",
    )
    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Skip fetching official pages to fill missing catalog deadlines",
    )
    parser.add_argument(
        "--enrich-max-items",
        type=int,
        default=0,
        help="Max undated catalog rows to enrich (0 = all)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    failures: list[str] = []
    soft_failures: list[str] = []
    try:
        sources = (
            [
                "global_competitions",
                "field_coverage_catalog",
                "expanded_catalog",
                "solid_programs_catalog",
                "mun_catalog",
                "dated_regional_catalog",
                "pathways_to_science",
                "devpost",
                "competition_sciences",
            ]
            if args.source == "all"
            else [args.source]
        )
        for source in sources:
            print(f"\n=== {source} ===")
            try:
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
            except Exception:
                # Live sites are frequently blocked / flaky in CI; soft-fail on --source all.
                soft = is_soft_fail_source(args.source, source)
                if soft:
                    soft_failures.append(source)
                    logger.exception(
                        "Source %s failed (soft-fail); continuing so maintenance still runs",
                        source,
                    )
                    print(f"Scrape FAILED for {source} (soft-fail); continuing.")
                else:
                    failures.append(source)
                    logger.exception(
                        "Source %s failed; continuing with remaining work", source
                    )
                    print(f"Scrape FAILED for {source} (see logs above); continuing.")
                try:
                    db.rollback()
                except Exception:
                    logger.exception("Could not rollback after %s failure", source)

        if not args.skip_enrichment and args.source in (
            "all",
            "field_coverage_catalog",
            "expanded_catalog",
            "solid_programs_catalog",
            "mun_catalog",
            "dated_regional_catalog",
            "global_competitions",
        ):
            print("\n=== enrich_catalog_deadlines ===")
            try:
                with CurlClient(delay_seconds=args.delay) as client:
                    enrich_stats = enrich_catalog_deadlines(
                        db,
                        client,
                        max_items=args.enrich_max_items,
                        delay_seconds=args.delay,
                    )
                print("Enrichment finished:")
                for key, value in enrich_stats.items():
                    print(f"  {key}: {value}")
            except Exception:
                # Enrichment is best-effort; never block country backfill / deactivation.
                logger.exception(
                    "Deadline enrichment failed (soft-fail); continuing to maintenance"
                )
                print("Enrichment FAILED (soft-fail); continuing to maintenance.")
                try:
                    db.rollback()
                except Exception:
                    logger.exception("Could not rollback after enrichment failure")

        if not args.skip_maintenance:
            # On --source all, isolate each step so a field-backfill bug cannot skip
            # country backfill / deadline deactivation (and vice versa).
            soft_maint = args.source == "all"
            filled = _run_maintenance_step(
                "backfill_eligible_countries",
                lambda: backfill_eligible_countries(db),
                soft=soft_maint,
                db=db,
            )
            reclassified = _run_maintenance_step(
                "backfill_opportunity_fields",
                lambda: backfill_opportunity_fields(db),
                soft=soft_maint,
                db=db,
            )
            deactivated = _run_maintenance_step(
                "deactivate_past_deadlines",
                lambda: deactivate_past_deadlines(db),
                soft=soft_maint,
                db=db,
            )
            junk = _run_maintenance_step(
                "deactivate_unusable_titles",
                lambda: deactivate_unusable_titles(db),
                soft=soft_maint,
                db=db,
            )
            stale = _run_maintenance_step(
                "deactivate_stale_listings",
                lambda: deactivate_stale_listings(db),
                soft=soft_maint,
                db=db,
            )
            if filled is not None:
                print(f"\nMaintenance: backfilled countries on {filled} opportunit(ies)")
            if reclassified is not None:
                print(
                    f"Maintenance: reclassified fields on {reclassified} opportunit(ies)"
                )
            if deactivated is not None:
                print(
                    f"Maintenance: deactivated {deactivated} past-deadline opportunit(ies)"
                )
            if junk is not None:
                print(
                    f"Maintenance: deactivated {junk} unusable-title opportunit(ies)"
                )
            if stale is not None:
                print(
                    f"Maintenance: deactivated {stale} stale (unseen) opportunit(ies)"
                )
    finally:
        db.close()

    if soft_failures:
        joined = ", ".join(soft_failures)
        print(f"\nSoft-failed sources (non-fatal): {joined}")
        # GitHub Actions annotations surface in the workflow UI without failing the job.
        for source in soft_failures:
            print(
                f"::warning title=Scraper soft-fail::"
                f"{source} failed on this run; catalog seed/maintenance continued."
            )
        print(
            "::notice title=Scraper soft-fail summary::"
            f"{len(soft_failures)} live source(s) soft-failed: {joined}"
        )
    if failures:
        print(f"\nCompleted with failures: {', '.join(failures)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
