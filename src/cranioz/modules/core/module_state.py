"""ModuleState enum (see modules.md v10 §4.1)."""

from __future__ import annotations

from enum import Enum


class ModuleState(Enum):
    """Lifecycle state of a Module."""

    REGISTERED = "registered"
    LOADED = "loaded"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    FAILED = "failed"
