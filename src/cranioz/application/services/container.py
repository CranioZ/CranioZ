"""ServiceContainer Protocol and a reference empty implementation.

A ServiceContainer resolves Service instances by type. The full
implementation (with SESSION/PROJECT scopes, module ownership,
disposal) is delivered later. This module provides the Protocol and an
``EmptyServiceContainer`` that refuses all lookups, useful for tests
that do not depend on service resolution.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class ServiceContainer(Protocol):
    """Resolves Service instances by type.

    The container is the only way a Module obtains Application-layer
    services. It is not a service locator: it is an explicit dependency
    container, injected through ``ModuleContext``.

    The full contract (scope: SESSION/PROJECT, lifecycle tied to the
    Module and to the Project) is defined in ``modules.md`` v10 §6.2
    and implemented in a later piece.
    """

    def resolve(self, service_type: type[T]) -> T: ...

    def contains(self, service_type: type) -> bool: ...


class ServiceNotFoundError(Exception):
    """Raised by ``ServiceContainer.resolve`` for unknown types."""


class EmptyServiceContainer:
    """``ServiceContainer`` that contains nothing.

    Useful for tests that do not depend on service resolution.
    ``resolve`` raises ``ServiceNotFoundError``; ``contains`` returns
    False.
    """

    def resolve(self, service_type: type[T]) -> T:
        raise ServiceNotFoundError(f"no service registered for {service_type.__name__}")

    def contains(self, service_type: type) -> bool:
        return False
