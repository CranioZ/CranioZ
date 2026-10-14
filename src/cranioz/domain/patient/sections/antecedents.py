"""PatientAntecedents (§8 Antecedentes).

The patient's history beyond the current complaint, organized in
four subsections:

- §8.1 Histórico cirúrgico
- §8.2 Dispositivos e implantes
- §8.3 Antecedentes familiares
- §8.4 Saúde da mulher (conditional)

All fields are free-form text. Empty strings are accepted as the
default state.

The fields of §8.4 (``pregnancy_contraception`` and
``breastfeeding``) are meaningful only when the patient's sex is
``FEMALE``. This section does not enforce that rule, because it
depends on a field that lives in a different section
(``identity.sex``). The rule is enforced by the ``Patient``
aggregate. See ``Patient._validate_womens_health_applicability``.

See ADR-0004 §11 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatientAntecedents:
    """Antecedents of the patient (§8)."""

    # §8.1 Surgical history
    previous_surgeries: str = ""
    anesthesia_history: str = ""

    # §8.2 Devices and implants
    prostheses_implants: str = ""

    # §8.3 Family history
    family_history: str = ""

    # §8.4 Women's health (conditional; enforced by Patient)
    pregnancy_contraception: str = ""
    breastfeeding: str = ""
