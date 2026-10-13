"""CatalogLoader.

Loads translation catalog files from disk.

A catalog is a JSON file organized by language and functional area,
for example:

    translations/en/core.json
    translations/pt-BR/workspace.json

This module is intentionally minimal:

- It reads and parses a single JSON file.
- It does not cache.
- It does not decide which catalogs to load.
- It does not know about the TranslationService or the registry.

Caching and decision-making belong to the TranslationCatalogRegistry.

The loader does not validate the catalog structure beyond what the
JSON parser requires. Semantic validation is the responsibility of
the TranslationValidator (a separate tool, not part of the runtime).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CatalogLoaderError(Exception):
    """Raised when a catalog file cannot be read or parsed."""


class CatalogLoader:
    """Loads translation catalog files from a base directory.

    The base directory is the root of the translations tree, for
    example: src/cranioz/translations.
    """

    def __init__(self, base_dir: Path) -> None:
        if not base_dir.exists():
            raise CatalogLoaderError(f"catalog base directory not found: {base_dir}")
        if not base_dir.is_dir():
            raise CatalogLoaderError(
                f"catalog base path is not a directory: {base_dir}"
            )
        self._base_dir = base_dir

    @property
    def base_dir(self) -> Path:
        """Return the base directory for translation catalogs."""
        return self._base_dir

    def load(self, language: str, area: str) -> dict[str, Any]:
        """Load a catalog for the given language and functional area.

        Args:
            language: BCP 47 language identifier (e.g. "en", "pt-BR").
            area: functional area (e.g. "core", "workspace").

        Returns:
            The parsed JSON contents as a dict.

        Raises:
            CatalogLoaderError: if the file is missing, unreadable,
                malformed, or does not contain a JSON object.
        """
        if not language:
            raise CatalogLoaderError("language must not be empty")
        if not area:
            raise CatalogLoaderError("area must not be empty")

        path = self._base_dir / language / f"{area}.json"

        if not path.exists():
            raise CatalogLoaderError(f"catalog file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise CatalogLoaderError(f"invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise CatalogLoaderError(f"cannot read {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise CatalogLoaderError(
                f"catalog must be a JSON object: {path}"
            )
        return data
