"""Volume rendering presets for Viewport3DView.

Each preset is a pair of transfer functions:

- ``vtkColorTransferFunction``: maps scalar values (HU for CT) to RGB.
- ``vtkPiecewiseFunction``: maps scalar values to opacity (0.0-1.0).

The values are based on the VTK built-in presets (vtkBone,
vtkSoftTissue, etc.) and the InVesalius default presets. They are
reproduced here as Python code so that:

- They are versioned with the project.
- They can be tested without VTK's C++ presets.
- They can be tweaked per clinical need.

HU (Hounsfield Units) ranges (approximate):

- Air:          -1000
- Lung:          -700 to -500
- Fat:           -100 to -50
- Water:            0
- Soft tissue:    20 to 60
- Bone:          200 to 1000+ (compact bone up to 2000)

See scene.md §27 (presentation state), ADR-0003 (semantic colors).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPoint:
    """A single (scalar, r, g, b) control point."""

    scalar: float
    r: float
    g: float
    b: float


@dataclass(frozen=True)
class OpacityPoint:
    """A single (scalar, opacity) control point."""

    scalar: float
    opacity: float


@dataclass(frozen=True)
class VolumePreset:
    """A volume rendering preset: color + opacity transfer functions."""

    name: str
    label: str
    color_points: tuple[ColorPoint, ...]
    opacity_points: tuple[OpacityPoint, ...]
    # Default window/level for this preset (HU). Used by
    # set_window_level() if the caller does not provide values.
    default_window: float
    default_level: float


# ----- Presets -------------------------------------------------------

BONE = VolumePreset(
    name="bone",
    label="Bone",
    color_points=(
        ColorPoint(-1000.0, 0.0, 0.0, 0.0),
        ColorPoint(-500.0, 0.0, 0.0, 0.0),
        ColorPoint(-200.0, 0.0, 0.0, 0.0),
        ColorPoint(-50.0, 0.0, 0.0, 0.0),
        ColorPoint(50.0, 0.0, 0.0, 0.0),
        ColorPoint(200.0, 0.0, 0.0, 0.0),
        ColorPoint(300.0, 1.0, 0.0, 0.0),
        ColorPoint(500.0, 1.0, 1.0, 0.0),
        ColorPoint(1000.0, 1.0, 1.0, 1.0),
        ColorPoint(2000.0, 1.0, 1.0, 1.0),
    ),
    opacity_points=(
        OpacityPoint(-1000.0, 0.0),
        OpacityPoint(200.0, 0.0),
        OpacityPoint(300.0, 0.15),
        OpacityPoint(500.0, 0.5),
        OpacityPoint(1000.0, 0.8),
        OpacityPoint(2000.0, 0.9),
    ),
    default_window=2000.0,
    default_level=500.0,
)

SOFT_TISSUE = VolumePreset(
    name="soft_tissue",
    label="Soft Tissue",
    color_points=(
        ColorPoint(-1000.0, 0.0, 0.0, 0.0),
        ColorPoint(-200.0, 0.0, 0.0, 0.0),
        ColorPoint(-100.0, 1.0, 0.0, 0.0),
        ColorPoint(-50.0, 1.0, 0.5, 0.5),
        ColorPoint(0.0, 1.0, 0.8, 0.8),
        ColorPoint(50.0, 1.0, 0.9, 0.9),
        ColorPoint(100.0, 1.0, 1.0, 1.0),
        ColorPoint(200.0, 1.0, 1.0, 1.0),
    ),
    opacity_points=(
        OpacityPoint(-1000.0, 0.0),
        OpacityPoint(-200.0, 0.0),
        OpacityPoint(-100.0, 0.02),
        OpacityPoint(0.0, 0.05),
        OpacityPoint(100.0, 0.1),
        OpacityPoint(200.0, 0.15),
    ),
    default_window=400.0,
    default_level=40.0,
)

SKIN = VolumePreset(
    name="skin",
    label="Skin",
    color_points=(
        ColorPoint(-1000.0, 0.0, 0.0, 0.0),
        ColorPoint(-500.0, 0.0, 0.0, 0.0),
        ColorPoint(-300.0, 0.0, 0.0, 0.0),
        ColorPoint(-100.0, 1.0, 0.8, 0.6),
        ColorPoint(0.0, 1.0, 0.9, 0.8),
        ColorPoint(100.0, 1.0, 0.95, 0.9),
        ColorPoint(500.0, 1.0, 1.0, 1.0),
    ),
    opacity_points=(
        OpacityPoint(-1000.0, 0.0),
        OpacityPoint(-300.0, 0.0),
        OpacityPoint(-100.0, 0.2),
        OpacityPoint(0.0, 0.4),
        OpacityPoint(100.0, 0.6),
        OpacityPoint(500.0, 0.8),
    ),
    default_window=600.0,
    default_level=300.0,
)

CT_ANGIO = VolumePreset(
    name="ct_angio",
    label="CT Angio",
    color_points=(
        ColorPoint(-1000.0, 0.0, 0.0, 0.0),
        ColorPoint(-500.0, 0.0, 0.0, 0.0),
        ColorPoint(-100.0, 0.0, 0.0, 0.0),
        ColorPoint(0.0, 0.0, 0.0, 0.0),
        ColorPoint(100.0, 1.0, 0.0, 0.0),
        ColorPoint(300.0, 1.0, 1.0, 0.0),
        ColorPoint(500.0, 1.0, 1.0, 1.0),
    ),
    opacity_points=(
        OpacityPoint(-1000.0, 0.0),
        OpacityPoint(0.0, 0.0),
        OpacityPoint(100.0, 0.1),
        OpacityPoint(300.0, 0.4),
        OpacityPoint(500.0, 0.7),
    ),
    default_window=600.0,
    default_level=300.0,
)

PRESETS: dict[str, VolumePreset] = {
    BONE.name: BONE,
    SOFT_TISSUE.name: SOFT_TISSUE,
    SKIN.name: SKIN,
    CT_ANGIO.name: CT_ANGIO,
}


def get_preset(name: str) -> VolumePreset:
    """Return the preset with the given name.

    Raises:
        KeyError: if the name is unknown.
    """
    try:
        return PRESETS[name]
    except KeyError as exc:
        raise KeyError(f"unknown volume preset: {name!r}; available: {sorted(PRESETS)!r}") from exc
