"""Global TranslationService instance (controlled singleton).

Widgets and UI code call ``get_translation_service()`` directly,
without receiving the service through a constructor. This avoids
threading the service through every widget's __init__.

To keep tests deterministic, the singleton is *controlled*:

- ``configure(service)`` replaces the current instance.
- ``reset()`` restores the default (an IdentityTranslationService).
- A test can install a controlled service in a fixture and reset
  it at teardown.

The module does not do any I/O at import time. The default instance
is created lazily on first access.
"""

from __future__ import annotations

from cranioz.infrastructure.i18n.translation_service import (
    IdentityTranslationService,
    TranslationService,
)

_instance: TranslationService | None = None


def get_translation_service() -> TranslationService:
    """Return the current global TranslationService.

    If no service has been configured yet, a default
    IdentityTranslationService is created and stored. The default
    returns the source text unchanged, which is safe: it never
    returns an internal key.
    """
    global _instance  # noqa: PLW0603
    if _instance is None:
        _instance = IdentityTranslationService()
    return _instance


def configure(service: TranslationService) -> None:
    """Install a new global TranslationService.

    Typically called once at application boot, after the catalogs
    have been discovered. It may also be called from tests to install
    a service backed by a controlled registry.

    Replaces the previous instance. The previous instance is not
    disposed: the TranslationService contract has no dispose method.
    """
    global _instance  # noqa: PLW0603
    _instance = service


def reset() -> None:
    """Restore the default (IdentityTranslationService).

    Intended for tests: a fixture may call reset() at teardown so
    that subsequent tests do not see a leaked service.
    """
    global _instance  # noqa: PLW0603
    _instance = None
