"""Guards for the 500-entry dated regional catalog."""

from __future__ import annotations

from scraper.sources.dated_regional_catalog import (
    DATED_REGIONAL_CATALOG,
    SOURCE_NAME,
    build_dated_regional_catalog,
)


def test_dated_regional_catalog_has_exactly_500_unique_entries() -> None:
    items = build_dated_regional_catalog()
    assert SOURCE_NAME == "dated_regional_catalog"
    assert len(items) == 500
    assert len({item.external_id for item in items}) == 500
    assert len(DATED_REGIONAL_CATALOG) == 500


def test_every_entry_has_deadline_and_region() -> None:
    for item in DATED_REGIONAL_CATALOG:
        assert item.deadline_at is not None, item.external_id
        assert item.eligible_countries is not None, item.external_id
        assert item.source_url
        assert item.title
