"""Canonical settings keys.

A closed set for the current phase. Adding a key requires a PR that
justifies the new setting, because ``set()`` rejects unknown keys.

Keys are dotted paths. The prefix identifies the subsystem that owns
the setting.
"""

from __future__ import annotations

APPEARANCE_THEME_MODE = "appearance.theme_mode"

# Professional Module presentation preferences. Profile data belongs in
# the dedicated SQLite database, never in this settings document.
PROFESSIONAL_UI_LAST_SECTION = "professional.ui.last_section"
PROFESSIONAL_UI_NAVIGATION_ORDER = "professional.ui.navigation_order"
PROFESSIONAL_UI_COLLAPSED_SECTIONS = "professional.ui.collapsed_sections"
PROFESSIONAL_UI_VISIBLE_SECTIONS = "professional.ui.visible_sections"

#: All keys recognized by the current phase. ``set()`` rejects others.
KNOWN_KEYS: frozenset[str] = frozenset(
    {
        APPEARANCE_THEME_MODE,
        PROFESSIONAL_UI_LAST_SECTION,
        PROFESSIONAL_UI_NAVIGATION_ORDER,
        PROFESSIONAL_UI_COLLAPSED_SECTIONS,
        PROFESSIONAL_UI_VISIBLE_SECTIONS,
    }
)
