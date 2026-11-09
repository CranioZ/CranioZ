"""SettingsService Protocol.

Defines the contract every settings backend must satisfy.

The contract is intentionally minimal:

- ``get(key, default)`` returns the stored value or ``default``.
- ``set(key, value)`` updates the in-memory state; it does NOT persist.
- ``save()`` persists the in-memory state.
- ``reload()`` re-reads the persisted state.
- ``changed`` is emitted after a successful ``set`` (in-memory) and
  after ``reload``.

Semantic validation of domain values (e.g. whether a string is a valid
``ThemeMode``) is the consumer's responsibility, not the SettingsService's.
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class SettingsService(Protocol):
    """Protocol implemented by every settings backend."""

    def get(self, key: str, default: T) -> T: ...

    def set(self, key: str, value: Any) -> None: ...

    def save(self) -> None: ...

    def reload(self) -> None: ...


# The concrete implementations are QObject subclasses (to expose the
# ``changed`` signal). A structural Protocol cannot express a PySide6
# signal cleanly without importing Qt into this module, so the Protocol
# covers only the method surface and the signal is documented here.
