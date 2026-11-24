"""Professional address value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    """Optional address fields for a professional or practice.

    Formatting and country-specific validation belong to the UI and
    regional-profile layers. The domain only rejects present fields
    that contain no meaningful text.
    """

    postal_code: str | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "postal_code",
            "street",
            "number",
            "complement",
            "district",
            "city",
            "state",
            "country",
        ):
            value = getattr(self, field_name)
            if value is not None and not value.strip():
                raise ValueError(f"{field_name} must not be whitespace only when set")
