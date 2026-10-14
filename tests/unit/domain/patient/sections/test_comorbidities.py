"""Tests for PatientComorbidities (§6 Comorbidades).

PatientComorbidities carries eleven free-form text fields, one per
comorbidity category.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.enums.comorbidity_category import (
    ComorbidityCategory,
)
from cranioz.domain.patient.sections.comorbidities import (
    PatientComorbidities,
)

# All eleven field names, in the same set as ComorbidityCategory.
_ALL_FIELDS = {
    "cardiovascular",
    "respiratory",
    "gastrointestinal",
    "hematological",
    "endocrine",
    "renal",
    "hepatic",
    "neurological",
    "musculoskeletal",
    "infectious_diseases",
    "others",
}


def test_comorbidities_defaults_are_empty_strings() -> None:
    c = PatientComorbidities()
    for field_name in _ALL_FIELDS:
        assert getattr(c, field_name) == ""


def test_comorbidities_holds_all_fields() -> None:
    c = PatientComorbidities(
        cardiovascular="Hypertension",
        respiratory="Asthma",
        gastrointestinal="",
        hematological="",
        endocrine="Diabetes type 2",
        renal="",
        hepatic="",
        neurological="",
        musculoskeletal="",
        infectious_diseases="",
        others="",
    )
    assert c.cardiovascular == "Hypertension"
    assert c.respiratory == "Asthma"
    assert c.endocrine == "Diabetes type 2"


def test_comorbidities_is_frozen() -> None:
    c = PatientComorbidities()
    attr = "cardiovascular"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(c, attr, "X")


def test_comorbidities_equality() -> None:
    a = PatientComorbidities(cardiovascular="X")
    b = PatientComorbidities(cardiovascular="X")
    assert a == b


def test_comorbidities_with_different_values_not_equal() -> None:
    a = PatientComorbidities(cardiovascular="X")
    b = PatientComorbidities(cardiovascular="Y")
    assert a != b


def test_fields_match_comorbidity_categories() -> None:
    """Every category has a corresponding field, and vice versa.

    The enum and the section are kept in sync: adding a category
    requires adding a field. This test guards against drift.
    """
    category_values = {c.value for c in ComorbidityCategory}
    assert category_values == _ALL_FIELDS
