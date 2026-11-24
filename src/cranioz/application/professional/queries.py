"""Read operations exposed by the Professional application layer."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cranioz.domain.professional.professional_profile import ProfessionalProfile


@runtime_checkable
class ProfessionalQueries(Protocol):
    """Read side for Professional consumers such as Editors."""

    def get_profile(self) -> ProfessionalProfile | None:
        """Return the installation profile, or ``None`` when not configured."""
        ...
