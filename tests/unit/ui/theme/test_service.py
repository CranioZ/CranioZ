"""Tests for ThemeService."""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.ui.theme.service import ThemeName, ThemeService


def test_default_theme_is_dark() -> None:
    service = ThemeService()
    assert service.theme is ThemeName.DARK


def test_with_theme_returns_new_instance() -> None:
    service = ThemeService()
    light = service.with_theme(ThemeName.LIGHT)
    assert light is not service
    assert light.theme is ThemeName.LIGHT
    assert service.theme is ThemeName.DARK  # original unchanged


def test_with_theme_is_idempotent_for_same_theme() -> None:
    service = ThemeService(theme=ThemeName.LIGHT)
    again = service.with_theme(ThemeName.LIGHT)
    assert again == service
    assert again is not service


def test_icon_name_is_identity() -> None:
    service = ThemeService()
    assert service.icon_name("log") == "log"
    assert service.icon_name("toggle") == "toggle"


def test_icon_name_is_theme_agnostic() -> None:
    dark = ThemeService(theme=ThemeName.DARK)
    light = ThemeService(theme=ThemeName.LIGHT)
    assert dark.icon_name("x") == light.icon_name("x")


def test_empty_icon_name_raises() -> None:
    service = ThemeService()
    with pytest.raises(ValueError, match="logical_name"):
        service.icon_name("")


def test_theme_name_members() -> None:
    expected = {"LIGHT", "DARK"}
    actual = {member.name for member in ThemeName}
    assert actual == expected


def test_theme_service_is_frozen() -> None:
    service = ThemeService()
    with pytest.raises(dataclasses.FrozenInstanceError):
        service.theme = ThemeName.LIGHT  # type: ignore[misc]
