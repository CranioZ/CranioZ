"""Contract: the UnicodeIconProvider catalog matches the spec."""

from cranioz.ui.icons.unicode import _DEFAULT_GLYPHS


def test_catalog_has_expected_count() -> None:
    # 60 canonical + 6 shell-specific = 66
    assert len(_DEFAULT_GLYPHS) == 66


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
    }
    assert required.issubset(_DEFAULT_GLYPHS.keys())
