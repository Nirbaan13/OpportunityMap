"""Tests for opportunity field classification."""

from __future__ import annotations

from scraper.parsers.field_mapping import (
    categories_to_field_slugs,
    classify_field_slugs,
    infer_field_slugs,
    refine_field_slugs,
)
from scraper.sources.devpost import THEME_TO_FIELDS, _themes_to_field_slugs


def test_education_theme_is_computer_science_not_social_science() -> None:
    assert THEME_TO_FIELDS["education"] == ["computer-science"]
    slugs = _themes_to_field_slugs(
        ["Education", "Beginner Friendly"],
        title="EdTech Builders Hackathon",
        description="Build tools that help students learn.",
    )
    assert "computer-science" in slugs
    assert "social-science" not in slugs


def test_devpost_health_theme_keeps_cs() -> None:
    slugs = _themes_to_field_slugs(
        ["Health"],
        title="MedHacks Online",
        description="Healthcare apps for patients.",
    )
    assert "computer-science" in slugs
    assert "biology" in slugs
    assert "social-science" not in slugs


def test_devpost_empty_themes_defaults_to_cs() -> None:
    slugs = _themes_to_field_slugs([], title="Weekly Online Hack")
    assert slugs == ["computer-science"]


def test_hackathon_keyword_infers_computer_science() -> None:
    assert "computer-science" in infer_field_slugs("Campus Hackathon 2026")


def test_education_alone_does_not_infer_social_science() -> None:
    slugs = infer_field_slugs("Education technology challenge for students")
    assert "social-science" not in slugs


def test_strong_social_science_still_inferred() -> None:
    slugs = infer_field_slugs("National Psychology Bowl and Model UN")
    assert "social-science" in slugs


def test_history_bee_inferred_but_bare_history_not() -> None:
    assert "social-science" in infer_field_slugs("National History Bee")
    assert "social-science" not in infer_field_slugs("Natural History Museum tour")


def test_refine_drops_social_science_on_hackathons() -> None:
    slugs = refine_field_slugs(
        ["social-science", "computer-science"],
        "Devpost Education Hackathon",
        "Tags: Education, Social Good",
        opportunity_type="hackathon",
    )
    assert "computer-science" in slugs
    assert "social-science" not in slugs


def test_refine_keeps_social_science_with_strong_signal() -> None:
    slugs = refine_field_slugs(
        ["social-science"],
        "Civics & Debate Hackathon",
        "Teams build tools for Model UN delegates",
        opportunity_type="hackathon",
    )
    assert "social-science" in slugs
    assert "computer-science" in slugs


def test_classify_hackathon_from_title_description() -> None:
    slugs = classify_field_slugs(
        "Google Solution Challenge",
        "Build SDG solutions with Google tech. Tags: Education",
        source_slugs=["social-science"],
        opportunity_type="hackathon",
    )
    assert "computer-science" in slugs
    assert "social-science" not in slugs


def test_category_law_does_not_match_lawrence() -> None:
    assert categories_to_field_slugs("Lawrence") == []
    assert categories_to_field_slugs("Law") == ["social-science"]


def test_category_ap_biology_partial_match() -> None:
    assert "biology" in categories_to_field_slugs("AP Biology")
