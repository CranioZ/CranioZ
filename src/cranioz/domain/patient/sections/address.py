"""PatientAddress (§4 Endereço).

The patient's address.

Every field is optional. A patient may not have an address on
record. The domain does not validate postal codes, street names, or
any other format: those are localization concerns that belong to
the UI layer.

See ADR-0004 §7 for the design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatientAddress:
    """Address of the patient (§4)."""

    postal_code: str | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
