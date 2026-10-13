"""CranioZ internationalization (i18n) infrastructure.

Public entry points:

- ``get_translation_service()``: return the active global service.
- ``configure(service)``: install a service (typically at boot).
- ``reset()``: restore the default (used by tests).
- ``tr(key, source_text, **params)``: convenience wrapper that calls
  the active service.

Usage in UI code::

    from cranioz.infrastructure.i18n import tr

    label = QLabel(tr("core.app.name", "CranioZ"))
"""

from __future__ import annotations

from typing import Any

from cranioz.infrastructure.i18n.instance import (
    configure,
    get_translation_service,
    reset,
)
from cranioz.infrastructure.i18n.translation_service import (
    CatalogTranslationService,
    IdentityTranslationService,
    TranslationService,
)

__all__ = [
    "CatalogTranslationService",
    "IdentityTranslationService",
    "TranslationService",
    "configure",
    "get_translation_service",
    "reset",
    "tr",
]


def tr(key: str, source_text: str, **params: Any) -> str:
    """Convenience wrapper around the active TranslationService.

    Calls ``get_translation_service().tr(key, source_text, **params)``.
    """
    return get_translation_service().tr(key, source_text, **params)
