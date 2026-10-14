"""PatientSex.

Sex of the patient, as recorded for clinical purposes.

This is distinct from gender identity. CranioZ records the
biological sex that is relevant to clinical planning (bone
densities, growth patterns, etc.). If gender identity becomes
relevant to the domain, it will be introduced as a separate field.

The enum uses three values:

- ``MALE``
- ``FEMALE``
- ``OTHER``   — recorded as such when the sex is not M / F, or when
  the clinician chooses not to classify the patient as either.

Additional values (e.g. ``UNKNOWN``) may be added later if the
domain requires them.
"""

from __future__ import annotations

from enum import Enum


class PatientSex(Enum):
    """Sex of the patient, as recorded for clinical purposes."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
