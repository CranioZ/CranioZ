"""Theme compilation.

Converts a ``ThemeTokens`` instance into ``CompiledStyles``: a QSS
string, a composed surface color map, and a typed elevation map.

The compiler is the single owner of global stylesheet main_window.
Widgets MUST NOT call ``QApplication.setStyleSheet`` themselves and
MUST NOT compose RGBA colors from tokens.

Specification: docs/architecture/appearance/themes-and-design-tokens.md §9

This module is the *only* place where token values are turned into
concrete Qt resources. The ``ThemeService`` delegates here.

Block 5.7 corrections:
- ``_compose_rgba`` emits ``rgba(r,g,b,X.XX%)`` (the CSS/QSS form
  documented by the Qt Style Sheets Reference). The previous decimal
  alpha form (``0.9200``) was accepted by Qt but was a non-standard
  extension.
- ``CompiledStyles`` wraps its maps in ``MappingProxyType`` so that
  consumers cannot mutate them. ``frozen=True`` alone was not enough
  (it freezes attribute reassignment, not the dicts themselves).
- ``_hex_to_rgb`` validates the exact 7-character ``#rrggbb`` shape
  with a regex, producing a useful error message instead of a
  generic ``int()`` ValueError.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

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

#: Strict #rrggbb pattern. The token validation already enforces this
#: shape, but the compiler is defence-in-depth: it may receive tokens
#: from a test or a future source that bypasses ``validate_tokens``.
_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Convert ``#rrggbb`` to an ``(r, g, b)`` tuple.

    Raises ``ValueError`` for anything else. Surface base colors are
    required to be ``#rrggbb`` by the token validation; this function
    is defence-in-depth for callers that bypass it.
    """
    if not _HEX_COLOR_RE.fullmatch(color):
        raise ValueError(f"Invalid color: {color!r}; expected #rrggbb")
    return (
        int(color[1:3], 16),
        int(color[3:5], 16),
        int(color[5:7], 16),
    )


def _compose_rgba(base: str, opacity: float) -> str:
    """Compose ``base`` with ``opacity`` into an ``rgba(r,g,b,X.XX%)`` string.

    Qt Style Sheets document the alpha channel as an integer 0-255 or
    a percentage. The decimal form (0.0-1.0) is a non-standard
    extension. We emit the percentage form for spec compliance.
    """
    r, g, b = _hex_to_rgb(base)
    alpha_percent = opacity * 100.0
    return f"rgba({r},{g},{b},{alpha_percent:.2f}%)"


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
    MUST NOT rely on the raw maps. The raw maps are read-only
    ``MappingProxyType`` instances: attempting to mutate them raises
    ``TypeError``. This is the contract that ``frozen=True`` alone
    does not enforce (it freezes attribute reassignment, not the
    mutable dicts stored in those attributes).
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
        surface_colors: dict[str, str] = {
            role: _compose_rgba(
                _base_color_for(tokens, role),
                getattr(tokens.surfaces, _SURFACE_OPACITY_TOKEN[role]),
            )
            for role in _SURFACE_OPACITY_TOKEN
        }
        elevations: dict[str, ElevationSpec] = {
            "panel": tokens.effects.elevation_panel,
            "dialog": tokens.effects.elevation_dialog,
            "overlay": tokens.effects.elevation_overlay,
        }
        qss = _build_qss(tokens)
        return CompiledStyles(
            theme_name=tokens.name,
            qss=qss,
            surface_colors=MappingProxyType(surface_colors),
            elevations=MappingProxyType(elevations),
        )

    def apply(self, styles: CompiledStyles) -> None:
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            _logger.warning(
                "ThemeCompiler.apply() called before QApplication exists; "
                "skipping global stylesheet main_window"
            )
            return
        app.setStyleSheet(styles.qss)


def _build_qss(tokens: ThemeTokens) -> str:
    """Build the global QSS string.

    Covers the shell: base surfaces, standard controls, table + header,
    scrollbars, buttons (default and primary/secondary classes), labels
    with roles, cards, and the StartButton / FlowRow classes used by the
    Home Page. Also covers the Workspace Areas (Block 5.5): Central
    Area with ``background_elevated``, lateral Areas with
    ``background_panel``, rounded corners, and an 8px splitter handle
    that acts as the gap between Areas. And the window control buttons
    (Block 5.6.1) with a flat OS-like style: transparent in the default
    state, neutral hover for minimize/maximize, red hover for close.
    """
    c = tokens.colors
    t = tokens.typography
    d = tokens.dimensions
    b = tokens.borders
    s = tokens.spacing

    # StartButton is a 56x56 circle; the radius is half the size.
    start_button_radius = 28

    # Block 5.5: Area backgrounds and rounded corners. The Central
    # Area is the lightest (background_elevated); lateral and bottom
    # Areas are darker (background_panel). The splitter handle is
    # painted with the window's base background so the gap reads as
    # empty space, not as a divider.
    area_central_bg = c.background_elevated
    area_side_bg = c.background_panel
    splitter_handle_bg = c.background_application
    area_radius = b.radius_panel

    return f"""
/* ----- Base ------------------------------------------------------ */
QWidget {{
    background-color: {c.background_application};
    color: {c.text_primary};
    font-family: {t.family_interface};
    font-size: {t.size_body}pt;
}}

QMainWindow, QDialog {{
    background-color: {c.background_application};
}}

/* ----- Workspace Areas (Block 5.5) ------------------------------- */
QWidget[area_placement="central"] {{
    background-color: {area_central_bg};
    border-radius: {area_radius}px;
}}

QWidget[area_placement="left"],
QWidget[area_placement="right"],
QWidget[area_placement="bottom"] {{
    background-color: {area_side_bg};
    border-radius: {area_radius}px;
}}

QSplitter::handle {{
    background-color: {splitter_handle_bg};
}}

QSplitter::handle:horizontal {{
    width: 8px;
}}

QSplitter::handle:vertical {{
    height: 8px;
}}

/* ----- TopOverlay (Top Bar) -------------------------------------- */
QFrame#top_overlay {{
    background-color: {c.background_application};
    border-radius: {area_radius}px;
}}

/* ----- Panels ---------------------------------------------------- */
QFrame#Panel, QWidget#Panel {{
    background-color: {c.background_panel};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_panel}px;
}}

/* ----- Cards ----------------------------------------------------- */
QFrame[class="card"] {{
    background-color: {c.background_panel};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_panel}px;
    padding: {s.md}px;
}}

QFrame[class="card_elevated"] {{
    background-color: {c.background_elevated};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_panel}px;
    padding: {s.md}px;
}}

/* ----- Home Page Dashboard Containers ---------------------------- */
QWidget#home_page_project_table, QWidget#home_page_flow_list, QWidget#home_page_community_sidebar {{
    background-color: {c.background_panel};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_panel}px;
    margin: {s.xs}px {s.sm}px;
    padding: {s.sm}px;
}}

/* ----- Toolbars -------------------------------------------------- */
QToolBar {{
    background-color: {c.background_panel};
    border: none;
    border-bottom: {b.width_default}px solid {c.border_default};
    spacing: {s.sm}px;
    padding: {s.xs}px {s.sm}px;
}}

QToolBar QToolButton {{
    background: transparent;
    border: none;
    border-radius: {b.radius_control}px;
    padding: {s.xs}px;
}}

QToolBar QToolButton:hover {{
    background-color: {c.background_elevated};
}}

QToolBar QToolButton:pressed {{
    background-color: {c.interactive_pressed};
}}

/* ----- Buttons --------------------------------------------------- */
QPushButton, QToolButton {{
    background-color: {c.interactive_default};
    color: {c.text_inverse};
    border: {b.width_default}px solid {c.interactive_default};
    border-radius: {b.radius_control}px;
    min-height: {d.control_height}px;
    padding: 0 {s.sm}px;
    font-weight: {t.weight_medium};
}}

QPushButton:hover, QToolButton:hover {{
    background-color: {c.interactive_hover};
    border-color: {c.interactive_hover};
}}

QPushButton:pressed, QToolButton:pressed {{
    background-color: {c.interactive_pressed};
    border-color: {c.interactive_pressed};
}}

QPushButton:disabled, QToolButton:disabled {{
    background-color: {c.background_elevated};
    color: {c.text_disabled};
    border-color: {c.border_default};
}}

/* Secondary buttons: outlined, neutral surface. */
QPushButton[class="secondary"], QToolButton[class="secondary"] {{
    background-color: {c.background_elevated};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_default};
}}

QPushButton[class="secondary"]:hover, QToolButton[class="secondary"]:hover {{
    background-color: {c.background_panel};
    border-color: {c.interactive_hover};
}}

/* IconSidebar: borderless navigation items centered in a narrow rail. */
QToolButton#CraniozIconSidebarItem {{
    background-color: transparent;
    border: none;
    border-radius: {b.radius_control}px;
    min-width: {d.control_height}px;
    max-width: {d.control_height}px;
    min-height: {d.control_height}px;
    max-height: {d.control_height}px;
    padding: 0;
    qproperty-iconSize: {d.icon_size}px {d.icon_size}px;
}}

QToolButton#CraniozIconSidebarItem:hover {{
    background-color: {c.background_elevated};
}}

QToolButton#CraniozIconSidebarItem:checked {{
    background-color: {c.background_elevated};
    border: {b.width_default}px solid {c.interactive_hover};
}}


/* FilePicker browse button: compact secondary variant.
   The objectName selector has higher specificity than the generic
   QToolButton rule, so it wins without needing !important. The
   fixed width set on the widget keeps the button from growing
   under the global padding. */
QToolButton#CraniozFilePickerBrowse {{
    background-color: {c.background_elevated};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_control}px;
    min-height: {d.control_height}px;
    max-height: {d.control_height}px;
    padding: 0;
    font-size: {t.size_body}pt;
}}

QToolButton#CraniozFilePickerBrowse:hover {{
    background-color: {c.background_panel};
    border-color: {c.interactive_hover};
}}

QToolButton#CraniozFilePickerBrowse:pressed {{
    background-color: {c.interactive_pressed};
    border-color: {c.interactive_pressed};
    color: {c.text_inverse};
}}


/* ----- Window control buttons (Block 5.6.1) --------------------- */
/* Flat buttons matching the Windows OS convention:
   - Transparent background in the default state.
   - Neutral hover for minimize and maximize.
   - Red hover for close.
   These selectors have higher specificity than the generic
   QPushButton rule, so the transparent background wins. */
QPushButton#home_page\\.top_bar\\.window_minimize,
QPushButton#home_page\\.top_bar\\.window_maximize,
QPushButton#home_page\\.top_bar\\.window_close,
QPushButton#workspace\\.top_bar\\.extras_segment\\.minimize,
QPushButton#workspace\\.top_bar\\.extras_segment\\.maximize,
QPushButton#workspace\\.top_bar\\.extras_segment\\.close {{
    background-color: transparent;
    border: none;
}}

QPushButton#home_page\\.top_bar\\.window_minimize:hover,
QPushButton#home_page\\.top_bar\\.window_maximize:hover,
QPushButton#workspace\\.top_bar\\.extras_segment\\.minimize:hover,
QPushButton#workspace\\.top_bar\\.extras_segment\\.maximize:hover {{
    background-color: {c.background_elevated};
}}

QPushButton#home_page\\.top_bar\\.window_close:hover,
QPushButton#workspace\\.top_bar\\.extras_segment\\.close:hover {{
    background-color: {c.feedback_error};
}}

QPushButton#home_page\\.top_bar\\.window_minimize:pressed,
QPushButton#home_page\\.top_bar\\.window_maximize:pressed,
QPushButton#workspace\\.top_bar\\.extras_segment\\.minimize:pressed,
QPushButton#workspace\\.top_bar\\.extras_segment\\.maximize:pressed {{
    background-color: {c.interactive_pressed};
}}

QPushButton#home_page\\.top_bar\\.window_close:pressed,
QPushButton#workspace\\.top_bar\\.extras_segment\\.close:pressed {{
    background-color: {c.feedback_error};
}}

/* ----- StartButton (floating circular action) ------------------- */
QPushButton#home_page_start_button {{
    background-color: {c.feedback_success};
    color: {c.text_inverse};
    border: 2px solid {c.interactive_hover};
    border-radius: {start_button_radius}px;
    font-size: 22px;
    font-weight: {t.weight_semibold};
    padding: 0;
}}

QPushButton#home_page_start_button:hover {{
    background-color: {c.feedback_success};
    border-color: {c.interactive_default};
}}

QPushButton#home_page_start_button:pressed {{
    background-color: {c.interactive_pressed};
}}

QPushButton#home_page_start_button:disabled {{
    background-color: {c.text_disabled};
    color: {c.background_application};
    border: 2px solid {c.border_default};
}}

/* ----- Inputs ---------------------------------------------------- */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
    background-color: {c.background_input};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_control}px;
    min-height: {d.control_height}px;
    padding: 0 {s.sm}px;
    selection-background-color: {c.interactive_selected};
    selection-color: {c.text_inverse};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: {b.width_focus}px solid {c.border_focus};
}}

QLineEdit::placeholder, QPlainTextEdit::placeholder {{
    color: {c.text_secondary};
}}

QComboBox::drop-down {{
    border: none;
    width: {d.control_height}px;
}}

QComboBox QAbstractItemView {{
    background-color: {c.background_elevated};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_default};
    selection-background-color: {c.interactive_selected};
    selection-color: {c.text_inverse};
}}

/* ----- Labels ---------------------------------------------------- */
QLabel {{
    color: {c.text_primary};
    background: transparent;
}}

QLabel[role="title"] {{
    font-size: {t.size_label}pt;
    font-weight: {t.weight_semibold};
    color: {c.text_primary};
}}

QLabel[role="subtitle"] {{
    font-size: {t.size_body}pt;
    color: {c.text_secondary};
}}

QLabel[role="caption"] {{
    font-size: {t.size_caption}pt;
    color: {c.text_secondary};
}}

QLabel[class="arrow"] {{
    color: {c.text_secondary};
    padding: 0 2px;
}}

/* ----- Tables ---------------------------------------------------- */
QTableWidget, QTableView {{
    background-color: {c.background_panel};
    alternate-background-color: {c.background_application};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_panel}px;
    gridline-color: {c.border_subtle};
    selection-background-color: {c.interactive_selected};
    selection-color: {c.text_inverse};
}}

QTableWidget::item, QTableView::item {{
    padding: {s.xs}px {s.sm}px;
    border: none;
}}

QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {c.interactive_selected};
    color: {c.text_inverse};
}}

QHeaderView {{
    background-color: {c.background_elevated};
    border: none;
}}

QHeaderView::section {{
    background-color: {c.background_elevated};
    color: {c.text_secondary};
    border: none;
    border-bottom: {b.width_default}px solid {c.border_default};
    border-right: {b.width_default}px solid {c.border_subtle};
    padding: {s.xs}px {s.sm}px;
    font-weight: {t.weight_medium};
}}

QHeaderView::section:last {{
    border-right: none;
}}

QTableCornerButton::section {{
    background-color: {c.background_elevated};
    border: none;
    border-bottom: {b.width_default}px solid {c.border_default};
}}

/* ----- Scrollbars ------------------------------------------------ */
QScrollBar:vertical {{
    background-color: {c.background_panel};
    width: 12px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {c.border_default};
    min-height: 24px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c.text_secondary};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
    border: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {c.background_panel};
    height: 12px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {c.border_default};
    min-width: 24px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {c.text_secondary};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
    border: none;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ----- FlowRow (Home Page flow list) ----------------------------- */
QFrame#home_page_flow_list_flow {{
    background-color: {c.background_elevated};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_control}px;
}}

QFrame#home_page_flow_list_flow:hover {{
    border-color: {c.interactive_hover};
}}

QFrame#home_page_flow_list_flow[checked="true"] {{
    background-color: {c.background_panel};
    border: {b.width_focus}px solid {c.border_focus};
}}

QFrame#home_page_flow_list_flow[checked="false"] {{
    background-color: {c.background_elevated};
    border: {b.width_default}px solid {c.border_default};
}}

QLabel#home_page_flow_list_step {{
    background-color: {c.background_input};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_subtle};
    border-radius: {b.radius_control}px;
    padding: 4px 8px;
}}

QFrame#home_page_flow_list_separator {{
    color: {c.border_default};
}}

/* ----- Misc ------------------------------------------------------ */
QToolTip {{
    background-color: {c.background_elevated};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_default};
    border-radius: {b.radius_control}px;
    padding: {s.xs}px {s.sm}px;
}}

QMenu {{
    background-color: {c.background_elevated};
    color: {c.text_primary};
    border: {b.width_default}px solid {c.border_default};
}}

QMenu::item:selected {{
    background-color: {c.interactive_selected};
    color: {c.text_inverse};
}}
""".strip()
