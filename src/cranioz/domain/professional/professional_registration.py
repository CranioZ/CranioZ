"""Professional registration entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfessionalRegistration:
    """A professional registration issued by an authority.

    Authority names are extensible rather than enum values. Country
    codes use the two-letter ISO 3166-1 form. Region codes, when used,
    use the ISO 3166-2 form and include the country prefix.
    """

    registration_id: str
    authority: str
    country_code: str
    registration_number: str
    region_code: str | None = None
    is_primary: bool = False

    def __post_init__(self) -> None:
        self._require_text(self.registration_id, "registration_id")
        self._require_text(self.authority, "authority")
        self._require_text(self.registration_number, "registration_number")

        country = self.country_code.strip().upper()
        if len(country) != 2 or not country.isalpha():
            raise ValueError("country_code must be a two-letter ISO 3166-1 code")
        object.__setattr__(self, "country_code", country)

        region = self.region_code.strip().upper() if self.region_code is not None else None
        if region is not None:
            if not region:
                raise ValueError("region_code must not be whitespace only when set")
            if not region.startswith(f"{country}-") or len(region) <= len(country) + 1:
                raise ValueError("region_code must use the ISO 3166-2 form")
        object.__setattr__(self, "region_code", region)

        authority = self.authority.strip().upper()
        object.__setattr__(self, "authority", authority)
        if authority == "CRM" and country == "BR" and region is None:
            raise ValueError("region_code is required for Brazilian CRM registrations")

        if not isinstance(self.is_primary, bool):
            raise TypeError("is_primary must be a bool")

    @staticmethod
    def _require_text(value: str, field_name: str) -> None:
        if not value:
            raise ValueError(f"{field_name} must not be empty")
        if not value.strip():
            raise ValueError(f"{field_name} must not be whitespace only")
