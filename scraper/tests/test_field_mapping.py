"""Tests for opportunity field classification."""

from __future__ import annotations

from scraper.parsers.field_mapping import (
    categories_to_field_slugs,
    classify_field_slugs,
    infer_field_slugs,
    looks_like_tech_social_mislabeled,
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


def test_real_social_science_program_keeps_tag() -> None:
    """Psychology / social-science research must not lose its field."""
    slugs = refine_field_slugs(
        ["social-science", "research"],
        "Summer Psychology Research Institute",
        "Residential program in psychology and sociology for rising seniors.",
        opportunity_type="program",
    )
    assert "social-science" in slugs
    assert "computer-science" not in slugs


def test_hackathon_education_classify_becomes_cs() -> None:
    slugs = classify_field_slugs(
        "Campus Education Hackathon",
        "Build EdTech apps for classrooms. Theme: Education",
        source_slugs=["social-science"],
        opportunity_type="hackathon",
    )
    assert "computer-science" in slugs
    assert "social-science" not in slugs


def test_non_hackathon_psychology_stays_social_science() -> None:
    slugs = classify_field_slugs(
        "AP Psychology Essay Contest",
        "Write about cognitive psychology and sociology.",
        source_slugs=["social-science", "writing"],
        opportunity_type="competition",
    )
    assert "social-science" in slugs
    assert "computer-science" not in slugs


def test_debate_and_model_un_do_not_gain_computer_science() -> None:
    for title, description in (
        ("National Debate Championship", "Policy debate tournament for high school."),
        ("Model UN Conference", "Delegate simulation of the United Nations."),
    ):
        slugs = classify_field_slugs(
            title,
            description,
            source_slugs=["social-science"],
            opportunity_type="competition",
        )
        assert "social-science" in slugs, title
        assert "computer-science" not in slugs, title
        assert not looks_like_tech_social_mislabeled(
            ["social-science"], title, description
        ), title


def test_refine_strips_ss_from_tech_competition_not_hackathon() -> None:
    slugs = refine_field_slugs(
        ["ai", "computer-science", "social-science", "business"],
        "Technovation",
        "Global programs where young people build AI and mobile solutions to community problems.",
        opportunity_type="competition",
    )
    assert "social-science" not in slugs
    assert "computer-science" in slugs
    assert "ai" in slugs
    assert "business" in slugs


def test_refine_does_not_force_cs_on_non_hackathon_tech_strip() -> None:
    slugs = refine_field_slugs(
        ["social-science", "ai"],
        "AI for Good challenges",
        "Applying machine learning to global development problems.",
        opportunity_type="competition",
    )
    assert "social-science" not in slugs
    assert "ai" in slugs
    # refine does not add CS for non-hackathons
    assert "computer-science" not in slugs


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
