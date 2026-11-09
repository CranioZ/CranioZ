"""ThemeService.

Runtime owner of the selected ``ThemeMode`` and the resolved ``ThemeName``.

Responsibilities (see themes-and-design-tokens.md §11):

- Resolve ``ThemeMode.SYSTEM`` into a concrete ``ThemeName`` via
  ``QStyleHints.colorScheme()``, with ``DARK`` as fallback.
- React to ``QStyleHints.colorSchemeChanged`` when ``SYSTEM`` is active
  and the signal exists on the platform.
- Expose the active ``ThemeTokens``.
- Expose convenience accessors: ``color(path)``, ``dimension(path)``,
  ``surface_color(role)``, and the legacy ``icon_name(logical_name)``.
- Compile and apply appearance resources via ``ThemeCompiler``.
- Persist the selected mode through ``SettingsService`` when the caller
  asks for it. ``set_mode`` does not save; the caller owns persistence.

The service does not own the settings file, does not read it directly,
and does not decide *when* to save.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any, cast

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QGuiApplication, QStyleHints

from cranioz.infrastructure.settings.keys import APPEARANCE_THEME_MODE
from cranioz.infrastructure.settings.protocol import SettingsService
from cranioz.ui.theme.compiler import CompiledStyles, ThemeCompiler
from cranioz.ui.theme.tokens import (
    THEME_TOKENS,
    ThemeMode,
    ThemeName,
    ThemeTokens,
)

_logger = logging.getLogger(__name__)


def _resolve_system_theme() -> ThemeName:
    """Resolve the operating-system preference into a ``ThemeName``.

    Falls back to ``DARK`` when the preference is unavailable or unknown.
    """
    raw_app = QGuiApplication.instance()
    if raw_app is None:
        return ThemeName.DARK
    app = cast(QGuiApplication, raw_app)
    style_hints = app.styleHints()
    try:
        scheme = style_hints.colorScheme()
    except AttributeError:
        # Older Qt versions do not expose colorScheme().
        return ThemeName.DARK
    scheme_name = getattr(scheme, "name", str(scheme))
    if scheme_name == "Dark":
        return ThemeName.DARK
    if scheme_name == "Light":
        return ThemeName.LIGHT
    return ThemeName.DARK


class ThemeService(QObject):
    """See module docstring."""

    theme_changed = Signal(ThemeName)

    def __init__(
        self,
        *,
        settings: SettingsService,
        default_mode: ThemeMode = ThemeMode.DARK,
        compiler: ThemeCompiler | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._compiler = compiler or ThemeCompiler()

        # Initial mode: the persisted preference, else the caller's default.
        persisted = self._settings.get(APPEARANCE_THEME_MODE, default_mode.value)
        try:
            self._mode = ThemeMode(persisted)
        except ValueError:
            _logger.warning(
                "invalid appearance.theme_mode %r; falling back to %s",
                persisted,
                default_mode.value,
            )
            self._mode = default_mode

        self._theme = self._resolve(self._mode)
        self._tokens = THEME_TOKENS[self._theme]
        self._compiled: CompiledStyles = self._compiler.compile(self._tokens)

        # SYSTEM reactivity, best effort.
        self._style_hints: QStyleHints | None = None
        self._color_scheme_connected = False
        if self._mode is ThemeMode.SYSTEM:
            self._try_connect_system_reactivity()

    # ----- Public contract (§11.1) ------------------------------------

    def mode(self) -> ThemeMode:
        return self._mode

    def set_mode(self, mode: ThemeMode) -> None:
        """Change the selected mode.

        Does not persist. The caller decides when to call
        ``settings.set(...)`` and ``settings.save()``.
        """
        if mode == self._mode:
            return
        self._mode = mode
        if mode is ThemeMode.SYSTEM:
            self._try_connect_system_reactivity()
        else:
            self._disconnect_system_reactivity()
        self._apply_theme(self._resolve(mode))

    def theme(self) -> ThemeName:
        return self._theme

    def tokens(self) -> ThemeTokens:
        return self._tokens

    def color(self, path: str) -> str:
        value = self._resolve_path(self._tokens.colors, path, "color")
        if not isinstance(value, str):
            raise TypeError(f"color token {path!r} is not a string: {type(value).__name__}")
        return value

    def dimension(self, path: str) -> int:
        value = self._resolve_path(self._tokens.dimensions, path, "dimension")
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"dimension token {path!r} is not an int: {type(value).__name__}")
        return value

    def surface_color(self, role: str) -> str:
        return self._compiled.surface_color(role)

    # ----- Convenience ------------------------------------------------

    def compiler(self) -> ThemeCompiler:
        return self._compiler

    def compiled(self) -> CompiledStyles:
        return self._compiled

    def icon_name(self, logical_name: str) -> str:
        """Return the concrete icon name for the active theme.

        Phase 2 behaviour is identity. Phase 8 (SVG icons) may map the
        logical name to a theme-specific asset.
        """
        if not logical_name:
            raise ValueError("logical_name must not be empty")
        return logical_name

    # ----- Internal: theme resolution and application ------------------

    def _resolve(self, mode: ThemeMode) -> ThemeName:
        if mode is ThemeMode.DARK:
            return ThemeName.DARK
        if mode is ThemeMode.LIGHT:
            return ThemeName.LIGHT
        return _resolve_system_theme()

    def _apply_theme(self, theme: ThemeName) -> None:
        self._theme = theme
        self._tokens = THEME_TOKENS[theme]
        self._compiled = self._compiler.compile(self._tokens)
        self._compiler.apply(self._compiled)
        self.theme_changed.emit(theme)

    # ----- Internal: system reactivity --------------------------------

    def _try_connect_system_reactivity(self) -> None:
        if self._color_scheme_connected:
            return
        raw_app = QGuiApplication.instance()
        if raw_app is None:
            return
        app = cast(QGuiApplication, raw_app)
        style_hints = app.styleHints()
        signal = getattr(style_hints, "colorSchemeChanged", None)
        if signal is None:
            _logger.info(
                "QStyleHints.colorSchemeChanged is unavailable; "
                "SYSTEM mode will not react to runtime OS changes"
            )
            return
        signal.connect(self._on_color_scheme_changed)
        self._style_hints = style_hints
        self._color_scheme_connected = True

    def _disconnect_system_reactivity(self) -> None:
        if not self._color_scheme_connected:
            return
        signal = getattr(self._style_hints, "colorSchemeChanged", None)
        if signal is not None:
            with contextlib.suppress(RuntimeError, TypeError):
                signal.disconnect(self._on_color_scheme_changed)
        self._style_hints = None
        self._color_scheme_connected = False

    def _on_color_scheme_changed(self, _scheme: Any) -> None:
        if self._mode is not ThemeMode.SYSTEM:
            return
        self._apply_theme(_resolve_system_theme())

    # ----- Internal: helpers ------------------------------------------

    def _resolve_path(self, section: Any, path: str, category: str) -> Any:
        value = section
        for part in path.split("."):
            try:
                value = getattr(value, part)
            except AttributeError as exc:
                raise KeyError(f"unknown {category} token {path!r}") from exc
        return value
