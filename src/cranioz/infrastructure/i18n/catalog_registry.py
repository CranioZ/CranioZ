"""TranslationCatalogRegistry.

Locates, loads, and caches translation catalogs by language and
functional area.

Design rules:

- Catalogs are loaded on demand. Nothing is loaded at construction.
- Loaded catalogs are cached in memory, keyed by (language, area).
- A failed load is not cached: the next request will retry.
- The registry does not decide the active language. That is the
  TranslationService's responsibility.
- The registry does not merge catalogs. It returns the catalog for
  a single (language, area) pair. The TranslationService decides how
  to resolve a fully qualified key across areas.
- The registry supports explicit cache invalidation for development
  and testing.

The registry is a thin layer over the CatalogLoader. Its only added
value is caching and the (language, area) key.
"""

from __future__ import annotations

from typing import Any

from cranioz.infrastructure.i18n.catalog_loader import (
    CatalogLoader,
    CatalogLoaderError,
)


class CatalogRegistryError(Exception):
    """Raised when a catalog cannot be resolved."""


class TranslationCatalogRegistry:
    """Caches translation catalogs by (language, area)."""

    def __init__(self, loader: CatalogLoader) -> None:
        self._loader = loader
        self._cache: dict[tuple[str, str], dict[str, Any]] = {}

    # ----- Public API -----------------------------------------------

    def get(self, language: str, area: str) -> dict[str, Any]:
        """Return the catalog for (language, area).

        Loads the catalog on first request and caches it. Subsequent
        requests for the same pair return the cached instance.

        Raises:
            CatalogRegistryError: if the catalog cannot be loaded.
        """
        key = (language, area)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            catalog = self._loader.load(language, area)
        except CatalogLoaderError as exc:
            raise CatalogRegistryError(
                f"cannot load catalog for language={language!r} "
                f"area={area!r}: {exc}"
            ) from exc

        self._cache[key] = catalog
        return catalog

    def has(self, language: str, area: str) -> bool:
        """Return True if the catalog is currently cached."""
        return (language, area) in self._cache

    def invalidate(self, language: str, area: str) -> None:
        """Remove a single entry from the cache.

        No-op if the entry is not cached.
        """
        self._cache.pop((language, area), None)

    def clear(self) -> None:
        """Remove all cached catalogs.

        Used during development and testing, or when the underlying
        catalog files change on disk and need to be reloaded.
        """
        self._cache.clear()

    def cached_keys(self) -> tuple[tuple[str, str], ...]:
        """Return the (language, area) pairs currently cached."""
        return tuple(self._cache.keys())
