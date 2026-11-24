"""Application service for the installation Professional profile."""

from __future__ import annotations

from cranioz.application.professional.repository import ProfessionalRepository
from cranioz.domain.professional.professional_profile import ProfessionalProfile


class ProfessionalService:
    """Single application owner of Professional profile persistence.

    The service is independent of project state. Consumers query it
    through ``ProfessionalQueries`` and mutate the profile through
    ``UpdateProfessionalProfileCommand``.
    """

    def __init__(self, repository: ProfessionalRepository) -> None:
        self._repository = repository
        self._repository.initialize()

    def get_profile(self) -> ProfessionalProfile | None:
        """Return the saved profile, or ``None`` before first configuration."""
        return self._repository.load_profile()

    def update_profile(self, profile: ProfessionalProfile) -> ProfessionalProfile:
        """Persist and return a validated profile aggregate."""
        if not isinstance(profile, ProfessionalProfile):
            raise TypeError("profile must be a ProfessionalProfile")
        self._repository.save_profile(profile)
        return profile
