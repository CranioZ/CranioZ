"""Tests for ComorbidityCategory."""

from __future__ import annotations

import pytest

from cranioz.domain.patient.enums.comorbidity_category import (
    ComorbidityCategory,
)


def test_members() -> None:
    expected = {
        "CARDIOVASCULAR",
        "RESPIRATORY",
        "GASTROINTESTINAL",
        "HEMATOLOGICAL",
        "ENDOCRINE",
        "RENAL",
        "HEPATIC",
        "NEUROLOGICAL",
        "MUSCULOSKELETAL",
        "INFECTIOUS_DISEASES",
        "OTHERS",
    }
    assert {m.name for m in ComorbidityCategory} == expected


def test_values() -> None:
    assert ComorbidityCategory.CARDIOVASCULAR.value == "cardiovascular"
    assert ComorbidityCategory.INFECTIOUS_DISEASES.value == "infectious_diseases"
    assert ComorbidityCategory.OTHERS.value == "others"


def test_lookup_by_value() -> None:
    assert ComorbidityCategory("cardiovascular") is ComorbidityCategory.CARDIOVASCULAR
    assert ComorbidityCategory("others") is ComorbidityCategory.OTHERS


def test_unknown_value_raises() -> None:
    with pytest.raises(ValueError):
        ComorbidityCategory("oncology")


def test_others_is_last_member() -> None:
    """OTHERS is the escape hatch and is listed last.

    The UI iterates over the categories in declaration order and
    presents OTHERS as the final option. This test documents and
    guards that ordering.
    """
    members = list(ComorbidityCategory)
    assert members[-1] is ComorbidityCategory.OTHERS
