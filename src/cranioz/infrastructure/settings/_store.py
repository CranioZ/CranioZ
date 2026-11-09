"""Internal: in-memory, key-path-aware settings store.

Shared by the filesystem and in-memory backends. Holds a flat mapping
of dotted keys to JSON-compatible values, plus the schema version.

Rules:
- The store never validates domain semantics.
- ``set`` rejects unknown keys.
- ``get`` returns the typed default when the value is missing or has an
  incompatible type, and logs a WARNING.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from cranioz.infrastructure.settings.keys import KNOWN_KEYS

T = TypeVar("T")

_logger = logging.getLogger(__name__)


def _is_compatible(value: Any, default: T) -> bool:  # noqa: UP047 - PEP 695 needs 3.12+
    """Return True if ``value`` is type-compatible with ``default``.

    JSON round-trips only produce ``dict``, ``list``, ``str``, ``int``,
    ``float``, ``bool`` and ``None``. We accept the same set, plus the
    usual Python numeric widening (int -> float) only when the default
    is explicitly float, to avoid silently turning ``True`` into ``1``.
    """
    if default is None:
        return value is None
    checkers: dict[type, Callable[[Any], bool]] = {
        bool: lambda v: isinstance(v, bool),
        int: lambda v: isinstance(v, int) and not isinstance(v, bool),
        float: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        str: lambda v: isinstance(v, str),
        list: lambda v: isinstance(v, list),
        dict: lambda v: isinstance(v, dict),
    }
    checker = checkers.get(type(default))
    if checker is None:
        return False
    return checker(value)


class SettingsStore:
    """In-memory representation of a settings document."""

    def __init__(self, schema_version: int) -> None:
        self._schema_version = schema_version
        self._values: dict[str, Any] = {}

    # ----- Schema -----------------------------------------------------

    @property
    def schema_version(self) -> int:
        return self._schema_version

    # ----- Access -----------------------------------------------------

    def get(self, key: str, default: T) -> T:
        if key not in self._values:
            return default
        value = self._values[key]
        if not _is_compatible(value, default):
            _logger.warning(
                "settings key %r has incompatible type %s; falling back to default %r",
                key,
                type(value).__name__,
                default,
            )
            return default
        return value  # type: ignore[no-any-return]

    def set(self, key: str, value: Any) -> None:
        if key not in KNOWN_KEYS:
            raise KeyError(f"unknown settings key: {key!r}")
        self._values[key] = value

    # ----- Serialization ---------------------------------------------

    def to_document(self) -> dict[str, Any]:
        """Return the flat key/value map grouped by the first path segment."""
        document: dict[str, Any] = {"schema_version": self._schema_version}
        for key, value in self._values.items():
            head, _, tail = key.partition(".")
            if not tail:
                raise AssertionError(f"settings key {key!r} has no dotted path")
            section = document.setdefault(head, {})
            if not isinstance(section, dict):
                raise AssertionError(f"settings section {head!r} collides with a flat value")
            section[tail] = value
        return document

    @classmethod
    def from_document(cls, document: dict[str, Any], schema_version: int) -> SettingsStore:
        """Build a store from a grouped document."""
        store = cls(schema_version)
        for head, section in document.items():
            if head == "schema_version":
                continue
            if not isinstance(section, dict):
                _logger.warning("ignoring non-object settings section %r", head)
                continue
            for tail, value in section.items():
                key = f"{head}.{tail}"
                if key not in KNOWN_KEYS:
                    _logger.warning("ignoring unknown settings key %r", key)
                    continue
                store._values[key] = value
        return store
