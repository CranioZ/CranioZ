"""IconProvider Protocol.

The contract every icon provider (Unicode, SVG, ...) must satisfy.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from PySide6.QtGui import QIcon

from cranioz.ui.icons.state import IconState


@runtime_checkable
class IconProvider(Protocol):
    """Provides QIcons and text glyphs by logical name and state."""

    def icon(
        self,
        name: str,
        size: int | None = None,
        state: IconState = IconState.DEFAULT,
    ) -> QIcon: ...

    def text_glyph(self, name: str) -> str: ...

    def invalidate_cache(self) -> None: ...
