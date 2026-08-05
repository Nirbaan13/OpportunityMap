"""Guards for the core STEM + business/economics catalog."""

from __future__ import annotations

from collections import Counter

from scraper.sources.core_stem_business_catalog import (
    CORE_STEM_BUSINESS_CATALOG,
    SOURCE_NAME,
    build_core_stem_business_catalog,
)


def test_core_stem_business_catalog_shape() -> None:
    items = build_core_stem_business_catalog()
    assert SOURCE_NAME == "core_stem_business_catalog"
    assert len(items) == 240
    assert len({item.external_id for item in items}) == 240
    assert len(CORE_STEM_BUSINESS_CATALOG) == 240

    counts = Counter(item.field_slugs[0] for item in items)
    assert counts == {
        "mathematics": 40,
        "physics": 40,
        "chemistry": 40,
        "biology": 40,
        "business": 40,
        "economics": 40,
    }


def test_every_entry_has_deadline_and_region() -> None:
    for item in CORE_STEM_BUSINESS_CATALOG:
        assert item.deadline_at is not None, item.external_id
        assert item.eligible_countries is not None, item.external_id
        assert item.source_url
        assert item.title
