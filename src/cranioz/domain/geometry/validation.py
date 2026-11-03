"""Structured validation findings for geometry.

A ``ValidationResult`` records the outcome of validating a mesh
against a profile. The initial implementation only needs the
``ValidationSeverity`` enum and the two dataclasses; the actual
profile registry and per-operation rules are introduced in later
phases of the Geometry Infrastructure document.

See the ``Geometry Infrastructure`` architecture document, §7.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(Enum):
    """Severity of a validation finding.

    - ERROR:   invalid for the requested operation; blocks commit.
    - WARNING: potential issue; acceptance depends on the operation's
               validation policy.
    - INFO:    informational finding; does not block commit.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A single validation finding."""

    code: str
    severity: ValidationSeverity
    message: str
    affected_elements: tuple[int, ...] = ()
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("ValidationIssue.code must not be empty")
        if not self.message:
            raise ValueError("ValidationIssue.message must not be empty")


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """The outcome of validating geometry against a profile."""

    is_valid: bool
    issues: tuple[ValidationIssue, ...]
    metrics: Mapping[str, float]
    profile_id: str
    profile_version: str
    source_revision_id: str | None = None

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise ValueError("ValidationResult.profile_id must not be empty")
        if not self.profile_version:
            raise ValueError("ValidationResult.profile_version must not be empty")

    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity is ValidationSeverity.ERROR)

    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity is ValidationSeverity.WARNING)

    def infos(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity is ValidationSeverity.INFO)
