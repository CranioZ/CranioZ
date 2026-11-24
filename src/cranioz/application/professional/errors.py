"""Application errors for the Professional profile."""


class ProfessionalError(Exception):
    """Base class for Professional application errors."""


class ProfessionalRepositoryError(ProfessionalError):
    """Base class for failures at the Professional persistence boundary."""


class ProfessionalStorageError(ProfessionalRepositoryError):
    """The Professional repository could not complete an operation."""


class ProfessionalCorrupted(ProfessionalRepositoryError):
    """The persisted Professional profile cannot be reconstructed."""
