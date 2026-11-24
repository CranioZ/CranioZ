"""Commands and handler for Professional profile mutations."""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.application.commands.base import Command
from cranioz.application.professional.service import ProfessionalService
from cranioz.domain.professional.professional_profile import ProfessionalProfile


@dataclass(frozen=True, kw_only=True)
class UpdateProfessionalProfileCommand(Command):
    """Create or replace the installation Professional profile."""

    profile: ProfessionalProfile
    is_reversible: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.profile, ProfessionalProfile):
            raise TypeError("profile must be a ProfessionalProfile")


class UpdateProfessionalProfileHandler:
    """Execute ``UpdateProfessionalProfileCommand`` through the service."""

    def __init__(self, service: ProfessionalService) -> None:
        self._service = service

    def handle(self, command: UpdateProfessionalProfileCommand) -> ProfessionalProfile:
        return self._service.update_profile(command.profile)
