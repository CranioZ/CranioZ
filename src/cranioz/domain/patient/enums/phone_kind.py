"""PhoneKind.

Kind of phone number recorded for the patient.

The domain only distinguishes the kind for presentation and
contact-preference purposes. The number itself is stored as a
free-form string because phone formats vary by country and by
operator.

The set of kinds is deliberately small and generic: it does not
encode country-specific categories (e.g., "celular" vs. "fixo"),
because those are labels for the same underlying kinds. The
user-facing labels ("Mobile", "Home", "Work", "Other") are
provided by the i18n layer, keyed by the enum value.

``MOBILE`` is the default kind, because mobile numbers are the
primary contact method in modern clinical records.

See ADR-0004 §5 for the design rationale.
"""

from __future__ import annotations

from enum import Enum


class PhoneKind(Enum):
    """Kind of phone number."""

    MOBILE = "mobile"
    HOME = "home"
    WORK = "work"
    OTHER = "other"
