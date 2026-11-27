"""Canonical SVG asset catalog for application icons."""

from __future__ import annotations

from pathlib import Path
from typing import Final

# Logical icon names are stable widget-facing identifiers. Paths are relative
# to ``assets/icons`` and may be reorganized without changing widget code.
SVG_ICON_ASSETS: Final[dict[str, str]] = {
    # Main window controls.
    "window_minimize": "main_window/minimize.svg",
    "window_maximize": "main_window/maximize.svg",
    "window_fullscreen": "main_window/fullscreen.svg",
    "window_restore": "main_window/restore.svg",
    "window_close": "main_window/close.svg",
    # Home page.
    "cranioz": "home_page/cranioz/cranioz.svg",
    "sidebar_toggle": "home_page/top_bar/side_navigation.svg",
    "help": "home_page/top_bar/help.svg",
    "logs": "home_page/top_bar/terminal.svg",
    "settings": "home_page/top_bar/settings_applications.svg",
    "community": "home_page/community/community.svg",
    "library": "home_page/community/library_objects.svg",
    "news": "home_page/community/news.svg",
    "feedback": "home_page/community/improve.svg",
    "contribute": "home_page/community/contribute.svg",
    "start": "home_page/botttom_bar/next.svg",
    "forward": "home_page/botttom_bar/next.svg",
    # Workspace shell.
    "toggle_left": "workspace/home_segment/dock_to_left.svg",
    "menu": "workspace/home_segment/menu.svg",
    "home": "workspace/home_segment/home.svg",
    "more_options": "workspace/extra_segment/more_options.svg",
    "toggle_bottom": "workspace/extra_segment/dock_to_bottom.svg",
    "toggle_right": "workspace/extra_segment/dock_to_right.svg",
    "new": "workspace/modules_segment/add_module.svg",
    # Professional module.
    "professional_profile": ("modules/professional/professional/professional.svg"),
    "document_templates": "modules/professional/documents/docs.svg",
    "budget": "modules/professional/budgets/wallet.svg",
    "schedule": "modules/professional/schedule/calendar.svg",
    "procedures": "modules/professional/procedures/procedures.svg",
    "professional_settings": "modules/professional/settings/settings.svg",
}


def svg_icon_path(name: str, icons_root: Path) -> Path:
    """Resolve an icon name against the catalog.

    The flat ``<name>.svg`` lookup is retained for custom providers and
    incremental assets that have not yet been added to the catalog.
    """
    relative_path = SVG_ICON_ASSETS.get(name)
    if relative_path is not None:
        return icons_root / relative_path
    return icons_root / f"{name}.svg"
