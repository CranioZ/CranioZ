"""Canonical settings keys.

A closed set for the current phase. Adding a key requires a PR that
justifies the new setting, because ``set()`` rejects unknown keys.

Keys are dotted paths. The prefix identifies the subsystem that owns
the setting.
"""

from __future__ import annotations

APPEARANCE_THEME_MODE = "appearance.theme_mode"

#: All keys recognized by the current phase. ``set()`` rejects others.
KNOWN_KEYS: frozenset[str] = frozenset(
    {
        APPEARANCE_THEME_MODE,
    }
)
