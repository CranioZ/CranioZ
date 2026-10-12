"""Tests for OverlaySpec."""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.overlay_spec import (
    OverlaySpec,
    OverlaySpecError,
)


def test_overlay_spec_holds_fields() -> None:
    spec = OverlaySpec(
        overlay_id="overlay.steps",
        title="Steps Panel",
        target_region=Placement.CENTRAL,
    )
    assert spec.overlay_id == "overlay.steps"
    assert spec.title == "Steps Panel"
    assert spec.target_region is Placement.CENTRAL


def test_empty_overlay_id_raises() -> None:
    with pytest.raises(OverlaySpecError, match="overlay_id"):
        OverlaySpec(
            overlay_id="",
            title="X",
            target_region=Placement.CENTRAL,
        )


def test_empty_title_raises() -> None:
    with pytest.raises(OverlaySpecError, match="title"):
        OverlaySpec(
            overlay_id="overlay.x",
            title="",
            target_region=Placement.CENTRAL,
        )