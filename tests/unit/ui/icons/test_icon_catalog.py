"""Contract: the UnicodeIconProvider catalog matches the spec."""

from cranioz.ui.icons.catalog import SVG_ICON_ASSETS
from cranioz.ui.icons.unicode import _DEFAULT_GLYPHS


def test_catalog_contains_required_names() -> None:
    required = {
        "home",
        "menu",
        "close",
        "settings",
        "help",
        "start",
        "forward",
        "community",
        "library",
        "news",
        "feedback",
        "contribute",
        "toggle_left",
        "toggle_right",
        "toggle_bottom",
        "new",
        "eye-open",
        "eye-closed",
        "clear",
        "drag",
        "professional_profile",
        "document_templates",
        "budget",
        "schedule",
        "procedures",
        "more_options",
        "professional_settings",
        "window_fullscreen",
        "cranioz",
        "logs",
    }
    assert required.issubset(_DEFAULT_GLYPHS.keys())


def test_catalog_has_expected_count() -> None:
    # 60 canonical + 6 Professional + 9 shell + 5 window + 1 toggle
    # + 4 L.0.2 additions + 4 Home Page project/flow actions = 89
    assert len(_DEFAULT_GLYPHS) == 89


def test_svg_catalog_names_have_unicode_fallbacks() -> None:
    assert set(SVG_ICON_ASSETS).issubset(_DEFAULT_GLYPHS)
