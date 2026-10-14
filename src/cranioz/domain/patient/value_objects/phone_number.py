"""PhoneNumber.

A phone number with its kind.

The number is stored as a free-form string: the domain does not
enforce a specific format, because formats vary by country and by
operator. Normalization and display masking belong to the UI layer.

The number is required and non-empty. A value consisting only of
whitespace is rejected: it is almost always a data-entry error, not
a legitimate number.

The ``kind`` field defaults to ``MOBILE``, the most common case in
modern clinical records.

See ADR-0004 §5 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.domain.patient.enums.phone_kind import PhoneKind


@dataclass(frozen=True)
class PhoneNumber:
    """A phone number and its kind."""

    number: str
    kind: PhoneKind = PhoneKind.MOBILE

    def __post_init__(self) -> None:
        if not self.number:
            raise ValueError("number must not be empty")
        if not self.number.strip():
            raise ValueError("number must not be whitespace only")
