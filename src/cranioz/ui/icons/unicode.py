"""UnicodeIconProvider.

Phase 2 implementation of IconProvider. It maps logical icon names
to Unicode glyphs and renders them into QIcons via QPainter.

The catalog is the closed set of 60 names from
`docs/architecture/appearance/icons/icons_and_icon_manager.md` §6,
plus 6 additional names required by the shell migration (5 for the
CommunitySidebar and 1 for the StartButton).

Spec: docs/architecture/appearance/icons/icons_and_icon_manager.md
"""

from __future__ import annotations

import logging
from typing import Final

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.icons.state import IconState
from cranioz.ui.theme.service import ThemeService

_logger = logging.getLogger(__name__)

#: Canonical catalog of 66 icon names.
#: 60 from the spec §6, plus 6 added for shell widgets.
_DEFAULT_GLYPHS: Final[dict[str, str]] = {
    # 6.1 Navigation (8)
    "home": "⌂",
    "menu": "☰",
    "close": "✕",
    "maximize": "▣",
    "restore": "▢",
    "back": "←",
    "forward": "→",
    "sidebar_toggle": "▤",
    # 6.2 Area Toggles (4)
    "toggle_left": "◧",
    "toggle_right": "◨",
    "toggle_bottom": "⬓",
    "toggle_top": "⬒",
    # 6.3 Actions (10)
    "new": "＋",  # noqa: RUF001 - fullwidth plus is intentional for the catalog
    "open": "📂",
    "save": "💾",
    "save_as": "📥",
    "delete": "🗑",
    "duplicate": "⧉",
    "export": "↗",
    "import": "↘",
    "print": "🖨",
    "search": "⌕",
    # 6.4 Feedback (4)
    "info": "ℹ",  # noqa: RUF001 - information source glyph is intentional
    "success": "✓",
    "warning": "⚠",
    "error": "✕",
    # 6.5 2D Tools (10)
    "cursor": "↖",
    "pan": "✋",
    "zoom_in": "⊕",
    "zoom_out": "⊖",
    "probe_hu": "⊙",
    "measure_distance": "📏",
    "measure_angle": "📐",
    "crosshair": "⊕",
    "ruler": "📏",
    "annotation": "✎",
    # 6.6 3D Tools (8)
    "rotate": "↻",
    "translate": "✥",
    "scale": "⤢",
    "cut": "✂",
    "paint": "🖌",
    "roi": "▭",
    "lock_rotation": "🔒",
    "unlock_rotation": "🔓",
    # 6.7 Modules (6)
    "module_tomography": "🩻",
    "module_registration": "⚏",
    "module_cephalometry": "👤",
    "module_segmentation": "▨",
    "module_osteotomy": "🔪",
    "module_guides": "🧩",
    # 6.8 Objects (6)
    "object_volume": "◉",
    "object_mesh": "◈",
    "object_landmark": "◆",
    "object_mask": "▩",
    "object_measurement": "📐",
    "object_group": "▤",
    # 6.9 System (4)
    "settings": "⚙",
    "help": "?",
    "about": "ⓘ",
    "log": "☰",
    # Additional names for shell widgets (Sprint F).
    "community": "👥",
    "library": "📚",
    "news": "📰",
    "feedback": "✉",
    "contribute": "♥",
    "start": "▶",
}


class UnicodeIconProvider(IconProvider):
    """Renders Unicode glyphs into QIcons, theme-aware."""

    def __init__(
        self,
        theme_service: ThemeService,
        glyph_map: dict[str, str] | None = None,
    ) -> None:
        self._theme_service = theme_service
        self._glyphs = glyph_map if glyph_map is not None else _DEFAULT_GLYPHS

    def text_glyph(self, name: str) -> str:
        glyph = self._glyphs.get(name)
        if glyph is None:
            _logger.warning(
                "UnicodeIconProvider: unknown icon name %r; using fallback '?'",
                name,
            )
            return "?"
        return glyph

    def icon(
        self,
        name: str,
        size: int | None = None,
        state: IconState = IconState.DEFAULT,
    ) -> QIcon:
        resolved_size = size if size is not None else self._theme_service.dimension("icon_size")
        color = self._color_for_state(state)
        return self._render_glyph(self.text_glyph(name), resolved_size, color)

    def invalidate_cache(self) -> None:
        """No-op: the provider does not cache icons."""

    def _color_for_state(self, state: IconState) -> QColor:
        token = {
            IconState.DEFAULT: "text_primary",
            IconState.HOVER: "interactive_hover",
            IconState.PRESSED: "interactive_pressed",
            IconState.SELECTED: "interactive_default",
            IconState.DISABLED: "text_disabled",
        }[state]
        return QColor(self._theme_service.color(token))

    @staticmethod
    def _render_glyph(glyph: str, size: int, color: QColor) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        font = QFont()
        font.setPixelSize(int(size * 0.75))
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, glyph)
        painter.end()
        return QIcon(pixmap)
