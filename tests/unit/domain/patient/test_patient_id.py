"""Tests for PatientId.

PatientId is a frozen value object that identifies a Patient
within the CranioZ application. These tests exercise its
validation, equality, hashing, and representation.

The tests do not depend on Qt, filesystem, or infrastructure.
They run in pure Python.
"""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.domain.patient.value_objects.patient_id import PatientId

# ----- Construction -------------------------------------------------


def test_patient_id_holds_value() -> None:
    pid = PatientId("abc-123")
    assert pid.value == "abc-123"


def test_patient_id_is_frozen() -> None:
    pid = PatientId("abc")
    attr = "value"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(pid, attr, "other")


# ----- Validation ---------------------------------------------------


def test_empty_value_raises() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        PatientId("")


def test_whitespace_only_value_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        PatientId("   ")


def test_tab_and_newline_value_raises() -> None:
    with pytest.raises(ValueError, match="whitespace"):
        PatientId("\t\n")


def test_value_with_surrounding_whitespace_is_accepted() -> None:
    # The domain does not trim; it only rejects values that are
    # entirely whitespace. A value with meaningful content and
    # surrounding spaces is preserved as-is.
    pid = PatientId("  abc  ")
    assert pid.value == "  abc  "


# ----- Equality -----------------------------------------------------


def test_equality_by_value() -> None:
    a = PatientId("abc")
    b = PatientId("abc")
    assert a == b


def test_different_ids_are_not_equal() -> None:
    assert PatientId("abc") != PatientId("xyz")


def test_equality_with_other_type_returns_false() -> None:
    assert PatientId("abc") != "abc"
    assert PatientId("abc") != 123


# ----- Hashing ------------------------------------------------------


def test_patient_id_is_hashable() -> None:
    # Frozen dataclasses are hashable, which makes PatientId usable
    # as a dict key. This matters for the Project domain, which
    # references patients by id.
    d = {PatientId("a"): 1, PatientId("b"): 2}
    assert d[PatientId("a")] == 1


def test_equal_ids_have_equal_hashes() -> None:
    a = PatientId("abc")
    b = PatientId("abc")
    assert hash(a) == hash(b)


# ----- Representation -----------------------------------------------


def test_str_returns_value() -> None:
    assert str(PatientId("abc-123")) == "abc-123"


def test_repr_mentions_value() -> None:
    text = repr(PatientId("abc-123"))
    assert "abc-123" in text
    assert "PatientId" in text
