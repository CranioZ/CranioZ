"""PatientRace.

Self-declared race/color of the patient, following the categories
used by the Brazilian IBGE. This is a clinical and epidemiological
field: race correlates with clinical outcomes and is recorded for
that purpose, not for identification.

The field is required at the domain level and defaults to
``NOT_DECLARED``. This makes "not declared" an explicit value,
distinct from "not applicable" and distinct from a missing field.

The enum identifiers and values are in English, consistent with
the rest of the CranioZ codebase. The user-facing labels
("Branca", "Parda", "Preta", "Amarela", "Indígena", "Não
declarada") are provided by the i18n layer, keyed by the enum
value.

See ADR-0004 §4 for the design rationale.
"""

from __future__ import annotations

from enum import Enum


class PatientRace(Enum):
    """Self-declared race/color of the patient (IBGE categories)."""

    WHITE = "white"
    BROWN = "brown"
    BLACK = "black"
    YELLOW = "yellow"
    INDIGENOUS = "indigenous"
    NOT_DECLARED = "not_declared"
