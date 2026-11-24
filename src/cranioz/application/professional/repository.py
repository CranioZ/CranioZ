"""Persistence port for the Professional profile."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cranioz.domain.professional.professional_profile import ProfessionalProfile


@runtime_checkable
class ProfessionalRepository(Protocol):
    """Persistence operations needed by ``ProfessionalService``.

    The port uses domain values only. Implementations must translate
    infrastructure failures into the ``ProfessionalRepositoryError``
    family and must not validate domain invariants.
    """

    def initialize(self) -> None:
        """Prepare storage before the first read or write.

        Raises:
            ProfessionalStorageError: storage cannot be initialized.
        """
        ...

    def load_profile(self) -> ProfessionalProfile | None:
        """Return the installation profile, or ``None`` when not configured.

        Raises:
            ProfessionalCorrupted: persisted data violates the domain.
            ProfessionalStorageError: storage cannot be read.
        """
        ...

    def save_profile(self, profile: ProfessionalProfile) -> None:
        """Atomically create or replace the installation profile.

        Saving a profile replaces its registration set as one operation.

        Raises:
            ProfessionalStorageError: storage cannot save the profile.
        """
        ...
