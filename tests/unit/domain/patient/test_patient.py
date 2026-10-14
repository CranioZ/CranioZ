"""Tests for Patient.

Patient is the aggregate root of the Patient domain. It carries the
PatientId, nine section value objects, and the cross-section
invariants. This file tests:

- Construction with the nine sections
- Equality and hashing by PatientId
- The women's health cross-section invariant
- Convenience methods: display_name, age, summary
- Representation

The tests do not depend on Qt, filesystem, or infrastructure.
"""

from __future__ import annotations

from datetime import date

import pytest

from cranioz.domain.patient.enums.patient_sex import PatientSex
from cranioz.domain.patient.patient import Patient
from cranioz.domain.patient.patient_summary import PatientSummary
from cranioz.domain.patient.sections.address import PatientAddress
from cranioz.domain.patient.sections.antecedents import PatientAntecedents
from cranioz.domain.patient.sections.comorbidities import (
    PatientComorbidities,
)
from cranioz.domain.patient.sections.complaint import PatientComplaint
from cranioz.domain.patient.sections.documents import PatientDocuments
from cranioz.domain.patient.sections.filiation import PatientFiliation
from cranioz.domain.patient.sections.habits import PatientHabits
from cranioz.domain.patient.sections.identity import PatientIdentity
from cranioz.domain.patient.sections.medications import PatientMedications
from cranioz.domain.patient.value_objects.patient_id import PatientId

# ----- Helpers ------------------------------------------------------


def _patient(
    patient_id: str = "pat-001",
    *,
    full_name: str = "Gabriel Silva",
    social_name: str | None = None,
    birth_date: date | None = None,
    sex: PatientSex | None = None,
    pregnancy_contraception: str = "",
    breastfeeding: str = "",
) -> Patient:
    """Build a Patient with sensible defaults.

    Only the fields relevant to a given test are overridden via
    keyword arguments. Every section is present, even if empty.
    """
    return Patient(
        patient_id=PatientId(patient_id),
        identity=PatientIdentity(
            full_name=full_name,
            social_name=social_name,
            birth_date=birth_date,
            sex=sex,
        ),
        documents=PatientDocuments(),
        filiation=PatientFiliation(),
        address=PatientAddress(),
        complaint=PatientComplaint(),
        comorbidities=PatientComorbidities(),
        medications=PatientMedications(),
        antecedents=PatientAntecedents(
            pregnancy_contraception=pregnancy_contraception,
            breastfeeding=breastfeeding,
        ),
        habits=PatientHabits(),
    )


# ----- Construction -------------------------------------------------


def test_patient_holds_id_and_sections() -> None:
    patient = _patient()
    assert patient.patient_id == PatientId("pat-001")
    assert patient.identity.full_name == "Gabriel Silva"
    assert isinstance(patient.documents, PatientDocuments)
    assert isinstance(patient.antecedents, PatientAntecedents)


def test_patient_can_be_built_with_minimal_sections() -> None:
    patient = _patient()
    # Every section is a value object, even if empty.
    assert patient.documents.document_type is None
    assert patient.filiation.father_name is None
    assert patient.address.city is None
    assert patient.complaint.chief_complaint == ""
    assert patient.comorbidities.cardiovascular == ""
    assert patient.medications.allergies == ""
    assert patient.antecedents.previous_surgeries == ""
    assert patient.habits.smoking == ""


# ----- Equality and hashing ----------------------------------------


def test_two_patients_with_same_id_are_equal() -> None:
    a = _patient("pat-001", full_name="Gabriel Silva")
    b = _patient("pat-001", full_name="Gabriel S. Silva")
    # Different names, same id → same patient.
    assert a == b


def test_two_patients_with_different_ids_are_not_equal() -> None:
    a = _patient("pat-001")
    b = _patient("pat-002")
    assert a != b


def test_patient_equality_with_other_type_returns_false() -> None:
    patient = _patient()
    assert patient != "pat-001"
    assert patient != 42


def test_patient_hash_is_based_on_id() -> None:
    a = _patient("pat-001")
    b = _patient("pat-001")
    assert hash(a) == hash(b)


def test_patient_can_be_used_in_a_set() -> None:
    a = _patient("pat-001")
    b = _patient("pat-001")  # same id
    c = _patient("pat-002")
    patients = {a, b, c}
    assert len(patients) == 2


def test_patient_can_be_used_as_dict_key() -> None:
    a = _patient("pat-001")
    b = _patient("pat-001")
    d = {a: "first"}
    # b is equal to a, so it resolves the same entry.
    assert d[b] == "first"


# ----- Women's health cross-section invariant ----------------------


def test_female_patient_can_have_womens_health_data() -> None:
    patient = _patient(
        sex=PatientSex.FEMALE,
        pregnancy_contraception="Not pregnant",
        breastfeeding="No",
    )
    assert patient.antecedents.pregnancy_contraception == "Not pregnant"
    assert patient.antecedents.breastfeeding == "No"


def test_female_patient_with_empty_womens_health_data_is_valid() -> None:
    # The fields are optional even for female patients.
    patient = _patient(sex=PatientSex.FEMALE)
    assert patient.antecedents.pregnancy_contraception == ""
    assert patient.antecedents.breastfeeding == ""


def test_male_patient_with_pregnancy_contraception_raises() -> None:
    with pytest.raises(ValueError, match="pregnancy_contraception"):
        _patient(
            sex=PatientSex.MALE,
            pregnancy_contraception="X",
        )


def test_male_patient_with_breastfeeding_raises() -> None:
    with pytest.raises(ValueError, match="breastfeeding"):
        _patient(
            sex=PatientSex.MALE,
            breastfeeding="X",
        )


def test_other_patient_with_pregnancy_contraception_raises() -> None:
    with pytest.raises(ValueError, match="pregnancy_contraception"):
        _patient(
            sex=PatientSex.OTHER,
            pregnancy_contraception="X",
        )


def test_patient_with_sex_none_with_pregnancy_contraception_raises() -> None:
    with pytest.raises(ValueError, match="pregnancy_contraception"):
        _patient(
            sex=None,
            pregnancy_contraception="X",
        )


def test_patient_with_sex_none_with_breastfeeding_raises() -> None:
    with pytest.raises(ValueError, match="breastfeeding"):
        _patient(
            sex=None,
            breastfeeding="X",
        )


def test_patient_with_sex_none_and_empty_womens_health_is_valid() -> None:
    # Not recorded sex, no women's health data: valid.
    patient = _patient(sex=None)
    assert patient.antecedents.pregnancy_contraception == ""
    assert patient.antecedents.breastfeeding == ""


# ----- display_name ------------------------------------------------


def test_display_name_falls_back_to_full_name() -> None:
    patient = _patient(full_name="Gabriel Silva", social_name=None)
    assert patient.display_name() == "Gabriel Silva"


def test_display_name_prefers_social_name() -> None:
    patient = _patient(full_name="Gabriel Silva", social_name="Gabi")
    assert patient.display_name() == "Gabi"


# ----- age ----------------------------------------------------------


def test_age_is_none_when_birth_date_is_none() -> None:
    patient = _patient(birth_date=None)
    assert patient.age() is None


def test_age_with_birthday_already_occurred() -> None:
    patient = _patient(birth_date=date(1990, 5, 12))
    # Reference: 2026-06-01. Birthday already occurred → 36.
    assert patient.age(at_date=date(2026, 6, 1)) == 36


def test_age_with_birthday_not_yet_occurred() -> None:
    patient = _patient(birth_date=date(1990, 12, 31))
    # Reference: 2026-06-01. Birthday not yet occurred → 35.
    assert patient.age(at_date=date(2026, 6, 1)) == 35


def test_age_on_birthday() -> None:
    patient = _patient(birth_date=date(1990, 5, 12))
    # Reference: 2026-05-12, exactly the birthday → 36.
    assert patient.age(at_date=date(2026, 5, 12)) == 36


def test_age_on_day_before_birthday() -> None:
    patient = _patient(birth_date=date(1990, 5, 12))
    # Reference: 2026-05-11, one day before → 35.
    assert patient.age(at_date=date(2026, 5, 11)) == 35


# ----- summary ------------------------------------------------------


def test_summary_returns_patient_summary() -> None:
    patient = _patient(
        patient_id="pat-007",
        full_name="Gabriel Silva",
        birth_date=date(1990, 5, 12),
        sex=PatientSex.MALE,
    )
    summary = patient.summary()
    assert isinstance(summary, PatientSummary)
    assert summary.patient_id == PatientId("pat-007")
    assert summary.display_name == "Gabriel Silva"
    assert summary.birth_date == date(1990, 5, 12)
    assert summary.sex is PatientSex.MALE


def test_summary_uses_display_name() -> None:
    patient = _patient(
        full_name="Gabriel Silva",
        social_name="Gabi",
    )
    summary = patient.summary()
    assert summary.display_name == "Gabi"


def test_summary_with_all_optional_fields_none() -> None:
    patient = _patient(birth_date=None, sex=None)
    summary = patient.summary()
    assert summary.birth_date is None
    assert summary.sex is None


# ----- Representation -----------------------------------------------


def test_repr_mentions_id_and_display_name() -> None:
    patient = _patient("pat-007", full_name="Gabriel Silva")
    text = repr(patient)
    assert "pat-007" in text
    assert "Gabriel Silva" in text


def test_repr_uses_social_name_when_present() -> None:
    patient = _patient(
        "pat-007",
        full_name="Gabriel Silva",
        social_name="Gabi",
    )
    assert "Gabi" in repr(patient)
