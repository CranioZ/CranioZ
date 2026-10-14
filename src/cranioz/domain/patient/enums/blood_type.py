"""BloodType.

Blood type of the patient, combining ABO group and Rh factor.

The domain uses a single value for the combination because the two
are always recorded together, always used together, and rarely
meaningful apart. Storing them as two fields would invite
inconsistent states, such as an ABO group without an Rh factor, or
an Rh factor without an ABO group.

``UNKNOWN`` is a valid value, distinct from "not applicable". At
the first consultation, the blood type may not yet be available.
The field is required at the domain level and defaults to
``UNKNOWN`` so that "not recorded" is an explicit value in the
persisted record, not a missing field.

The enum identifiers and values are in English, consistent with
the rest of the CranioZ codebase. The user-facing labels
("A+", "A-", "O+", "Desconhecido", ...) are provided by the i18n
layer, keyed by the enum value.

See ADR-0004 §4 for the design rationale.
"""

from __future__ import annotations

from enum import Enum


class BloodType(Enum):
    """Blood type combining ABO group and Rh factor."""

    A_POSITIVE = "a_positive"
    A_NEGATIVE = "a_negative"
    B_POSITIVE = "b_positive"
    B_NEGATIVE = "b_negative"
    AB_POSITIVE = "ab_positive"
    AB_NEGATIVE = "ab_negative"
    O_POSITIVE = "o_positive"
    O_NEGATIVE = "o_negative"
    UNKNOWN = "unknown"
