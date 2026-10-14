"""DocumentType.

Kind of identity document recorded for the patient, expressed as
a generic concept that is independent of the issuing country.

The domain stores the type, the country, and the number together
(in ``PatientDocuments``). It does not validate the format of the
number: that is a localization concern that belongs to the UI
layer (mask, validation messages).

The document type is deliberately generic:

- ``NATIONAL_ID`` covers RG (BR), DNI (ES), and equivalent
  national identity documents.
- ``TAX_ID`` covers CPF (BR), SSN (US), NIF (PT), and equivalent
  tax identification numbers.
- ``DRIVERS_LICENSE`` covers CNH (BR) and equivalent driving
  licenses.

The country-specific name and format (RG vs. DNI, CPF vs. SSN) is
resolved by the UI layer from the ``(document_type, country)``
pair, using the i18n catalogs. The domain never stores the
localized name as a technical identifier.

This design keeps the persisted representation stable across
locales and countries: a Brazilian patient's ``tax_id`` remains
``tax_id`` regardless of the active language or deployment country.

See ADR-0004 §5 for the design rationale.
"""

from __future__ import annotations

from enum import Enum


class DocumentType(Enum):
    """Generic kind of identity document, without country-specific encoding."""

    NATIONAL_ID = "national_id"
    TAX_ID = "tax_id"
    DRIVERS_LICENSE = "drivers_license"
    PASSPORT = "passport"
    BIRTH_CERTIFICATE = "birth_certificate"
    OTHER = "other"
