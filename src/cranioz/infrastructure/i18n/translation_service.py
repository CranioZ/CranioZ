"""TranslationService.

Resolves translation keys to localized strings.

This module defines:

- The ``TranslationService`` contract, as a Protocol.
- A concrete implementation, ``CatalogTranslationService``, backed
  by a TranslationCatalogRegistry.
- An ``IdentityTranslationService``, useful for tests and for the
  early phase of the application before catalogs exist.

The public API is a single method::

    service.tr(key, source_text, **params)

The ``source_text`` argument is mandatory (see the i18n documentation
§5). It provides a last-resort fallback when the key cannot be
resolved through the catalogs.

Fallback sequence (i18n doc §8):

1. Look up the message in the active language catalog.
2. If unavailable, look up the message in the English source catalog.
3. If unavailable, use the required English ``source_text``.
4. If no usable text can be produced, use a safe generic message.

Today the service supports simple named-parameter interpolation
("Hello {name}"). ICU MessageFormat (pluralization, select, etc.) is
intentionally not implemented yet: no message in the codebase
requires it. It will be added when the first plural message appears.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from cranioz.infrastructure.i18n.catalog_registry import (
    CatalogRegistryError,
    TranslationCatalogRegistry,
)

_logger = logging.getLogger(__name__)

SOURCE_LANGUAGE = "en"

# A safe generic message used as a last-resort fallback (step 4 of
# the fallback sequence). It is intentionally not translated: if the
# translation system cannot produce text, we must not depend on it.
_GENERIC_FALLBACK = "[translation unavailable]"


@runtime_checkable
class TranslationService(Protocol):
    """Contract for a translation service.

    Implementations must be able to:
    - return the active language;
    - change the active language;
    - resolve a translation key with a mandatory English source text.
    """

    @property
    def language(self) -> str: ...

    def set_language(self, language: str) -> None: ...

    def tr(self, key: str, source_text: str, **params: Any) -> str: ...


class CatalogTranslationService:
    """TranslationService backed by a TranslationCatalogRegistry.

    Keys are namespaced by functional area:

        "core.app.name"       → area "core",     path ["app", "name"]
        "workspace.area.x"    → area "workspace", path ["area", "x"]

    The first segment of the key selects the catalog. The remaining
    segments navigate the catalog tree to find an entry with a
    "message" field.

    If the key cannot be resolved through the active language catalog,
    the English catalog is tried. If that fails too, the required
    ``source_text`` is used. If even that is empty, a generic fallback
    message is returned and a diagnostic is logged.
    """

    def __init__(
        self,
        registry: TranslationCatalogRegistry,
        language: str = SOURCE_LANGUAGE,
    ) -> None:
        if not language:
            raise ValueError("language must not be empty")
        self._registry = registry
        self._language = language

    # ----- Language management --------------------------------------

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        """Change the active language.

        No catalogs are loaded here: they are loaded on demand by the
        registry. Changing the language is therefore cheap.

        Raises ValueError if the language is empty.
        """
        if not language:
            raise ValueError("language must not be empty")
        self._language = language

    # ----- Translation ----------------------------------------------

    def tr(self, key: str, source_text: str, **params: Any) -> str:
        """Resolve a translation key.

        Args:
            key: semantic translation key, for example
                "workspace.area.placeholder.empty".
            source_text: mandatory English source text. Used as the
                last-resort fallback when the key is not resolvable
                through the catalogs.
            **params: named parameters for interpolation.

        Returns:
            The localized string, with parameters interpolated.
        """
        if not key:
            raise ValueError("key must not be empty")

        message = self._resolve(key, source_text)

        try:
            return message.format(**params)
        except (KeyError, IndexError, ValueError) as exc:
            _logger.warning(
                "translation interpolation failed for key=%r: %s", key, exc
            )
            # Interpolation failure is a fallback event. Return the
            # source text unformatted so the user still sees something.
            return source_text or _GENERIC_FALLBACK

    # ----- Internals ------------------------------------------------

    def _resolve(self, key: str, source_text: str) -> str:
        """Apply the fallback sequence to resolve a key to a message."""
        message = self._lookup(self._language, key)
        if message is not None:
            return message

        if self._language != SOURCE_LANGUAGE:
            message = self._lookup(SOURCE_LANGUAGE, key)
            if message is not None:
                return message

        if source_text:
            return source_text

        _logger.error(
            "no usable translation for key=%r (language=%r)",
            key,
            self._language,
        )
        return _GENERIC_FALLBACK

    def _lookup(self, language: str, key: str) -> str | None:
        """Look up a key in the catalog of the given language.

        Returns the message string, or None if the catalog or key is
        unavailable.
        """
        area, *path = key.split(".")
        if not area or not path:
            return None

        try:
            catalog = self._registry.get(language, area)
        except CatalogRegistryError:
            return None

        node: Any = catalog
        for segment in path:
            if not isinstance(node, dict):
                return None
            node = node.get(segment)
            if node is None:
                return None

        if isinstance(node, dict):
            message = node.get("message")
            if isinstance(message, str):
                return message

        return None


class IdentityTranslationService:
    """TranslationService that returns the source_text unchanged.

    Useful for:
    - Tests that do not care about translations.
    - The early phase of the application before catalogs exist.
    - Fallback when no catalog registry is available.

    It supports the language property and set_language() so that
    callers see a consistent API, but changing the language has no
    effect on the returned text.
    """

    def __init__(self, language: str = SOURCE_LANGUAGE) -> None:
        if not language:
            raise ValueError("language must not be empty")
        self._language = language

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        if not language:
            raise ValueError("language must not be empty")
        self._language = language

    def tr(self, key: str, source_text: str, **params: Any) -> str:
        if not key:
            raise ValueError("key must not be empty")
        try:
            return source_text.format(**params)
        except (KeyError, IndexError, ValueError):
            return source_text or _GENERIC_FALLBACK
