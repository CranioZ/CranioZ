"""Widget-local fixtures that are not part of the central conftest."""

from __future__ import annotations

from typing import ClassVar

import pytest
from PySide6.QtGui import QIcon

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.icons.state import IconState


class NullIconProvider(IconProvider):
    """Provider whose ``icon()`` returns a null QIcon for every name.

    Used to force the ``text_glyph()`` fallback path in widgets that
    prefer icons when available.
    """

    _GLYPHS: ClassVar[dict[str, str]] = {
        "eye-open": "👁",
        "eye-closed": "⊘",
        "search": "⌕",
        "clear": "✕",
        "drag": "⋮⋮",
    }

    def icon(
        self,
        name: str,
        size: int | None = None,
        state: IconState = IconState.DEFAULT,
    ) -> QIcon:
        return QIcon()  # null

    def text_glyph(self, name: str) -> str:
        return self._GLYPHS.get(name, "?")

    def invalidate_cache(self) -> None:
        pass


@pytest.fixture
def null_icon_provider() -> IconProvider:
    return NullIconProvider()
