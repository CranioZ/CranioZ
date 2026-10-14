"""ComorbidityCategory.

Categories of comorbidities tracked in the patient's clinical
record. The list follows the sections shown in the patient module
prototype.

The enum is used by the UI to iterate over the categories with
translated labels, and by the domain to validate that no unknown
category is set on a ``PatientComorbidities`` value object.

Each category corresponds to one named field in
``PatientComorbidities``. The enum and the section are kept in
sync: adding a category here requires adding a field there, and
vice versa.

The category set is intentionally broad: each category aggregates
many specific conditions under a single free-form field. If a
category grows enough to need structured data (specific diagnoses
with codes, dates, severities), it will be promoted to its own
value object without affecting the other categories.

The identifiers and values are in English, consistent with the
rest of the CranioZ codebase. The user-facing labels
("Cardiovasculares", "Respiratórios", ...) are provided by the
i18n layer, keyed by the enum value.

See ADR-0004 §9 for the design rationale.
"""

from __future__ import annotations

from enum import Enum


class ComorbidityCategory(Enum):
    """Categories of comorbidities."""

    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    HEMATOLOGICAL = "hematological"
    ENDOCRINE = "endocrine"
    RENAL = "renal"
    HEPATIC = "hepatic"
    NEUROLOGICAL = "neurological"
    MUSCULOSKELETAL = "musculoskeletal"
    INFECTIOUS_DISEASES = "infectious_diseases"
    OTHERS = "others"
