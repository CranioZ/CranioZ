"""In-memory reference implementation of the Professional repository."""

from __future__ import annotations

from cranioz.domain.professional.professional_profile import ProfessionalProfile


class InMemoryProfessionalRepository:
    """Store the installation profile in memory for tests and previews."""

    def __init__(self) -> None:
        self._profile: ProfessionalProfile | None = None

    def initialize(self) -> None:
        return None

    def load_profile(self) -> ProfessionalProfile | None:
        return self._profile

    def save_profile(self, profile: ProfessionalProfile) -> None:
        self._profile = profile
