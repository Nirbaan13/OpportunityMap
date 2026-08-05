"""Guards for the 50-per-field expand catalog."""

from __future__ import annotations

from collections import Counter

from scraper.sources.field_expand_catalog import (
    FIELD_EXPAND_CATALOG,
    FIELDS,
    SOURCE_NAME,
    build_field_expand_catalog,
)


def test_field_expand_catalog_has_50_per_field() -> None:
    items = build_field_expand_catalog()
    assert SOURCE_NAME == "field_expand_catalog"
    assert len(items) == 600
    assert len({item.external_id for item in items}) == 600
    assert len(FIELD_EXPAND_CATALOG) == 600

    counts = Counter(item.field_slugs[0] for item in items)
    assert set(counts) == set(FIELDS)
    assert all(count == 50 for count in counts.values())


def test_every_entry_has_deadline_and_region() -> None:
    for item in FIELD_EXPAND_CATALOG:
        assert item.deadline_at is not None, item.external_id
        assert item.eligible_countries is not None, item.external_id
        assert item.source_url
        assert item.title
