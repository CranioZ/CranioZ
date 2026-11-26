"""Professional Module definition."""

from __future__ import annotations

from cranioz.application.professional import (
    ProfessionalService,
    UpdateProfessionalProfileCommand,
)
from cranioz.modules.builtin.professional.manifest import MANIFEST
from cranioz.modules.core.module import ModuleBase


class ProfessionalModule(ModuleBase):
    """Declarative contributions for the Professional Module."""

    manifest = MANIFEST

    def commands(self) -> tuple[type[UpdateProfessionalProfileCommand], ...]:
        return (UpdateProfessionalProfileCommand,)

    def services(self) -> tuple[type[ProfessionalService], ...]:
        return (ProfessionalService,)
