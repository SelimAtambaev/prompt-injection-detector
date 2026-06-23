"""Schema-consistency tests for the canonical taxonomy.

These guard the contract promised in THREAT_MODEL.md: the taxonomy is the
single source of truth, and supporting structures (severity map, helpers) must
stay aligned with it. They are cheap but catch label drift before it spreads.
"""

from app.detection.taxonomy import (
    DEFAULT_SEVERITY,
    TAXONOMY_VERSION,
    AttackCategory,
)


def test_severity_map_covers_every_category() -> None:
    # Every category must have a severity prior, and no extras.
    assert set(DEFAULT_SEVERITY.keys()) == set(AttackCategory)


def test_severity_values_in_unit_interval() -> None:
    assert all(0.0 <= v <= 1.0 for v in DEFAULT_SEVERITY.values())


def test_benign_is_zero_severity() -> None:
    assert DEFAULT_SEVERITY[AttackCategory.BENIGN] == 0.0


def test_attack_categories_excludes_benign() -> None:
    attacks = AttackCategory.attack_categories()
    assert AttackCategory.BENIGN not in attacks
    assert len(attacks) == len(AttackCategory) - 1


def test_category_values_are_unique_and_lowercase() -> None:
    values = [c.value for c in AttackCategory]
    assert len(values) == len(set(values))
    assert all(v == v.lower() for v in values)


def test_taxonomy_version_is_set() -> None:
    assert TAXONOMY_VERSION
