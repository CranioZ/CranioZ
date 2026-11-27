"""Contract: the UnicodeIconProvider catalog matches the spec."""

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
    }
    assert required.issubset(_DEFAULT_GLYPHS.keys())


def test_catalog_has_expected_count() -> None:
    # 60 canonical + 6 Professional + 7 shell + 4 window + 1 toggle
    # + 4 L.0.2 additions = 82
    assert len(_DEFAULT_GLYPHS) == 82
