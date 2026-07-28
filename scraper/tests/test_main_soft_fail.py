"""Soft-fail policy for --source all live network scrapers."""

from __future__ import annotations

from scraper.main import LIVE_NETWORK_SOURCES, is_soft_fail_source


def test_live_network_sources_cover_ci_flaky_sites() -> None:
    assert LIVE_NETWORK_SOURCES == {
        "pathways_to_science",
        "devpost",
        "competition_sciences",
    }


def test_soft_fail_only_on_source_all_for_live_sites() -> None:
    for source in LIVE_NETWORK_SOURCES:
        assert is_soft_fail_source("all", source)
        assert not is_soft_fail_source(source, source)


def test_catalog_seeds_are_hard_failures_on_source_all() -> None:
    for source in (
        "global_competitions",
        "field_coverage_catalog",
        "expanded_catalog",
    ):
        assert not is_soft_fail_source("all", source)
