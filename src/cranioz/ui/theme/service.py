"""ThemeService.

Provides theme-dependent resources to UI widgets.

In this phase the service is minimal: it exposes the active theme name
and resolves logical icon names into concrete icon identifiers.

Concrete visual styling (colors, fonts, spacing) is applied later via
Qt stylesheets. Widgets should never hardcode colors or icon paths;
they consult the ThemeService instead.

Rules:
- The service is stateless with respect to the application; it only
  reports the active theme and resolves icons.
- The service does not decide *when* the theme changes; that is the
  responsibility of a future settings/theme coordinator.
- The service does not know about individual widgets.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class ThemeName(Enum):
    """Identifier of the active theme."""

    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class ThemeService:
    """Resolves theme-dependent resources for UI widgets.

    The service is immutable. To change theme, create a new instance
    via `with_theme`.
    """

    theme: ThemeName = ThemeName.DARK

    def with_theme(self, theme: ThemeName) -> ThemeService:
        """Return a new ThemeService for the given theme."""
        return replace(self, theme=theme)

    def icon_name(self, logical_name: str) -> str:
        """Return the concrete icon name for the active theme.

        For now this is identity: the logical name is the icon name.
        Future themes may map 'log' to 'log_dark' or 'log_light'.

        Rules:
        - The logical name is what Tools declare in their specs.
        - The concrete name is what the UI loader will look up on disk.
        - The mapping depends only on the active theme.
        """
        if not logical_name:
            raise ValueError("logical_name must not be empty")
        return logical_name
