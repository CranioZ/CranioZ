"""SVG-backed icon provider with theme-aware recoloring."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from cranioz.ui.icons.catalog import svg_icon_path
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.icons.state import IconState, color_token_for_state
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeName

_logger = logging.getLogger(__name__)
_CURRENT_COLOR = "currentColor"


def default_svg_icons_root() -> Path:
    """Return the packaged root containing source SVG icons."""
    return Path(__file__).resolve().parents[2] / "assets" / "icons"


class SvgIconProvider(IconProvider):
    """Resolve SVG assets by logical name and fall back when unavailable.

    SVG assets use ``currentColor`` as their paint value. The provider
    substitutes the active theme/state color before rendering.
    """

    def __init__(
        self,
        theme_service: ThemeService,
        icons_root: Path,
        fallback_provider: IconProvider,
    ) -> None:
        self._theme_service = theme_service
        self._icons_root = icons_root
        self._fallback_provider = fallback_provider
        self._cache: dict[tuple[str, int, ThemeName, IconState], QIcon] = {}
        self._theme_service.theme_changed.connect(self._on_theme_changed)

    def icon(
        self,
        name: str,
        size: int | None = None,
        state: IconState = IconState.DEFAULT,
    ) -> QIcon:
        resolved_size = size if size is not None else self._theme_service.dimension("icon_size")
        theme = self._theme_service.theme()
        key = (name, resolved_size, theme, state)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        path = svg_icon_path(name, self._icons_root)
        if not path.is_file():
            _logger.debug(
                "SvgIconProvider: missing asset %r; using fallback",
                path,
            )
            return self._fallback_icon(key, name, size, state)

        color = self._theme_service.color(color_token_for_state(state))
        icon = self._render_svg(path, resolved_size, color)
        if icon is None:
            return self._fallback_icon(key, name, size, state)
        self._cache[key] = icon
        return icon

    def text_glyph(self, name: str) -> str:
        return self._fallback_provider.text_glyph(name)

    def invalidate_cache(self) -> None:
        self._cache.clear()
        self._fallback_provider.invalidate_cache()

    def _on_theme_changed(self, _theme: ThemeName) -> None:
        self.invalidate_cache()

    def _fallback_icon(
        self,
        key: tuple[str, int, ThemeName, IconState],
        name: str,
        size: int | None,
        state: IconState,
    ) -> QIcon:
        icon = self._fallback_provider.icon(name, size=size, state=state)
        self._cache[key] = icon
        return icon

    def _render_svg(self, path: Path, size: int, color: str) -> QIcon | None:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            _logger.exception("cannot read SVG icon %s; using fallback", path)
            return None

        if _CURRENT_COLOR not in source:
            _logger.error(
                "SVG icon %s does not declare currentColor; using fallback",
                path,
            )
            return None

        colored = QByteArray(source.replace(_CURRENT_COLOR, color).encode("utf-8"))
        renderer = QSvgRenderer(colored)
        if not renderer.isValid():
            _logger.error("invalid SVG icon %s; using fallback", path)
            return None

        ratio = 1.0
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            ratio = max(1.0, screen.devicePixelRatio())

        view_box = renderer.viewBoxF()
        if view_box.width() > 0 and view_box.height() > 0:
            pixel_width = max(1, round(size * (view_box.width() / view_box.height()) * ratio))
            pixel_height = max(1, round(size * ratio))
        else:
            pixel_width = max(1, round(size * ratio))
            pixel_height = pixel_width

        pixmap = QPixmap(pixel_width, pixel_height)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        try:
            renderer.render(painter, QRectF(0, 0, pixel_width, pixel_height))
        finally:
            painter.end()
        pixmap.setDevicePixelRatio(ratio)
        return QIcon(pixmap)
