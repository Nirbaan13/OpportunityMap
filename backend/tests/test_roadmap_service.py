from app.services.profile_service import yearly_target_for_grade
from app.services.roadmap_service import _is_strong
from app.services.matching_service import ScoredMatch
from app.schemas.profile import FieldOption


def test_yearly_targets_by_grade() -> None:
    assert yearly_target_for_grade(7) == 2
    assert yearly_target_for_grade(10) == 3
    assert yearly_target_for_grade(11) == 4
    assert yearly_target_for_grade(12) == 3


def test_strong_match_requires_all_interests() -> None:
    fields = [
        FieldOption(id=1, name="Math", slug="math"),
        FieldOption(id=2, name="Physics", slug="physics"),
    ]
    match = ScoredMatch(
        opportunity=None,  # type: ignore[arg-type]
        score=20,
        shared_fields=fields,
        reasons=[],
    )
    assert _is_strong(match, 2)
    assert not _is_strong(match, 3)
    assert not _is_strong(match, 0)
