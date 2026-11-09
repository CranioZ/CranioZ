"""Theme compilation.

Converts a ``ThemeTokens`` instance into ``CompiledStyles``: a QSS
string, a composed surface color map, and a typed elevation map.

The compiler is the single owner of global stylesheet application.
Widgets MUST NOT call ``QApplication.setStyleSheet`` themselves and
MUST NOT compose RGBA colors from tokens.

Specification: docs/architecture/appearance/themes-and-design-tokens.md §9

This module is the *only* place where token values are turned into
concrete Qt resources. The ``ThemeService`` delegates here.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication

from cranioz.ui.theme.tokens import (
    ElevationSpec,
    ThemeName,
    ThemeTokens,
)

_logger = logging.getLogger(__name__)


#: Surface roles whose base color is a fixed literal, independent of theme.
#: Per themes-and-design-tokens.md §6.2, the modal backdrop is always
#: black; only its opacity differs between themes.
_SURFACE_FIXED_BASE_COLOR: Mapping[str, str] = {
    "modal_backdrop": "#000000",
}

#: Surface roles whose base color comes from a ``ColorTokens`` attribute.
_SURFACE_BASE_COLOR_TOKEN: Mapping[str, str] = {
    "toolbar": "background_panel",
    "popover": "background_elevated",
}

#: Opacity token for each surface role. Every role in this map is a
#: supported surface; ``compile()`` iterates over its keys.
_SURFACE_OPACITY_TOKEN: Mapping[str, str] = {
    "toolbar": "opacity_toolbar",
    "popover": "opacity_popover",
    "modal_backdrop": "opacity_modal_backdrop",
}


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Convert ``#rrggbb`` to an ``(r, g, b)`` tuple.

    Raises ``ValueError`` for anything else. Surface base colors are
    required to be ``#rrggbb`` by the token validation.
    """
    if len(color) != 7 or not color.startswith("#"):
        raise ValueError(f"not a #rrggbb color: {color!r}")
    return (
        int(color[1:3], 16),
        int(color[3:5], 16),
        int(color[5:7], 16),
    )


def _compose_rgba(base: str, opacity: float) -> str:
    """Compose ``base`` with ``opacity`` into an ``rgba(r,g,b,a)`` string."""
    r, g, b = _hex_to_rgb(base)
    return f"rgba({r},{g},{b},{opacity:.4f})"


def _base_color_for(tokens: ThemeTokens, role: str) -> str:
    """Return the base color for a surface role."""
    fixed = _SURFACE_FIXED_BASE_COLOR.get(role)
    if fixed is not None:
        return fixed
    token_name = _SURFACE_BASE_COLOR_TOKEN[role]
    value = getattr(tokens.colors, token_name)
    if not isinstance(value, str):
        raise TypeError(
            f"surface role {role!r} base color token {token_name!r} "
            f"is not a string: {type(value).__name__}"
        )
    return value


@dataclass(frozen=True)
class CompiledStyles:
    """Opaque compiled appearance resources.

    Consumers access surfaces and elevations through the methods; they
    MUST NOT rely on the raw maps. The raw maps are exposed for tests
    and for the ``ThemeCompiler`` itself.
    """

    theme_name: ThemeName
    qss: str
    surface_colors: Mapping[str, str]
    elevations: Mapping[str, ElevationSpec]

    def surface_color(self, role: str) -> str:
        try:
            return self.surface_colors[role]
        except KeyError as exc:
            raise KeyError(
                f"unknown surface role {role!r}; known roles: {sorted(self.surface_colors)}"
            ) from exc

    def elevation(self, role: str) -> ElevationSpec:
        try:
            return self.elevations[role]
        except KeyError as exc:
            raise KeyError(
                f"unknown elevation role {role!r}; known roles: {sorted(self.elevations)}"
            ) from exc


class ThemeCompiler:
    """Compiles ``ThemeTokens`` into ``CompiledStyles``."""

    def compile(self, tokens: ThemeTokens) -> CompiledStyles:
        surface_colors = {
            role: _compose_rgba(
                _base_color_for(tokens, role),
                getattr(tokens.surfaces, _SURFACE_OPACITY_TOKEN[role]),
            )
            for role in _SURFACE_OPACITY_TOKEN
        }
        elevations = {
            "panel": tokens.effects.elevation_panel,
            "dialog": tokens.effects.elevation_dialog,
            "overlay": tokens.effects.elevation_overlay,
        }
        qss = _build_qss(tokens)
        return CompiledStyles(
            theme_name=tokens.name,
            qss=qss,
            surface_colors=surface_colors,
            elevations=elevations,
        )

    def apply(self, styles: CompiledStyles) -> None:
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            _logger.warning(
                "ThemeCompiler.apply() called before QApplication exists; "
                "skipping global stylesheet application"
            )
            return
        app.setStyleSheet(styles.qss)


def _build_qss(tokens: ThemeTokens) -> str:
    """Build the global QSS string.

    Phase 2 covers the base surface and the standard controls. Component
    styles are added as the widget library is implemented.
    """
    c = tokens.colors
    t = tokens.typography
    d = tokens.dimensions
    b = tokens.borders
    return f"""
QWidget {{
    background-color: {c.background_application};
    color: {c.text_primary};
    font-family: {t.family_interface};
    font-size: {t.size_body}pt;
}}

QMainWindow, QDialog {{
    background-color: {c.background_application};
}}

QFrame#Panel, QWidget#Panel {{
    background-color: {c.background_panel};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_panel}px;
}}

QToolBar {{
    background-color: {c.background_panel};
    border: none;
    border-bottom: {b.width_default}px solid {c.border_default};
}}

QPushButton, QToolButton {{
    background-color: {c.interactive_default};
    color: {c.text_inverse};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_control}px;
    min-height: {d.control_height}px;
    padding: 0 8px;
}}

QPushButton:hover, QToolButton:hover {{
    background-color: {c.interactive_hover};
}}

QPushButton:pressed, QToolButton:pressed {{
    background-color: {c.interactive_pressed};
}}

QPushButton:disabled, QToolButton:disabled {{
    background-color: {c.background_panel};
    color: {c.text_disabled};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
    background-color: {c.background_input};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_control}px;
    min-height: {d.control_height}px;
    padding: 0 6px;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: {b.width_focus}px solid {c.border_focus};
}}

QLabel {{
    color: {c.text_primary};
    background: transparent;
}}

QLabel[role="secondary"] {{
    color: {c.text_secondary};
}}

QToolTip {{
    background-color: {c.background_elevated};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_default};
    padding: 4px;
}}
""".strip()
