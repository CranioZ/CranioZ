"""Tests for the volume rendering presets."""

from __future__ import annotations

import pytest

from cranioz.ui.editors.viewport_3d.presets import (
    BONE,
    CT_ANGIO,
    PRESETS,
    SKIN,
    SOFT_TISSUE,
    get_preset,
)


def test_presets_dict_contains_expected_names() -> None:
    assert set(PRESETS) == {"bone", "soft_tissue", "skin", "ct_angio"}


def test_get_preset_returns_known() -> None:
    assert get_preset("bone") is BONE
    assert get_preset("soft_tissue") is SOFT_TISSUE
    assert get_preset("skin") is SKIN
    assert get_preset("ct_angio") is CT_ANGIO


def test_get_preset_unknown_raises() -> None:
    with pytest.raises(KeyError, match="unknown volume preset"):
        get_preset("does_not_exist")


@pytest.mark.parametrize("preset", PRESETS.values(), ids=PRESETS.keys())
def test_preset_has_non_empty_transfer_functions(preset) -> None:
    assert preset.color_points, f"{preset.name} has no color points"
    assert preset.opacity_points, f"{preset.name} has no opacity points"


@pytest.mark.parametrize("preset", PRESETS.values(), ids=PRESETS.keys())
def test_preset_window_is_positive(preset) -> None:
    assert preset.default_window > 0
