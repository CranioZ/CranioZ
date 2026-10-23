"""Application Services — service container contract (modules.md v10 §6.2).

A ServiceContainer owns the lifecycle of Service instances and resolves
them by type. Modules do not instantiate or dispose container-owned
services directly; they receive the container through ``ModuleContext``.

The full container (with scope: SESSION/PROJECT) is delivered in a
later piece. This module defines the Protocol and an ``EmptyServiceContainer``
for tests.
"""

from cranioz.application.services.container import (
    EmptyServiceContainer,
    ServiceContainer,
)

__all__ = [
    "EmptyServiceContainer",
    "ServiceContainer",
]
