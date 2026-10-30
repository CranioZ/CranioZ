"""Transform — rigid transformation (rotation + translation).

A Transform is a value object that represents a rigid transformation
in 3D space. It is used by the Scene to position objects relative to
their parent or to the Scene's global coordinate system.

For the first version, the transform is stored as:
- A translation vector (x, y, z) in millimetres.
- A rotation quaternion (w, x, y, z) representing the rotation.

The domain does not depend on NumPy, SciPy, or any math library.
The Transform is pure data; the actual matrix composition is
performed by the geometry layer (infrastructure).

Units: millimetres (mm). See scene.md §16.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Vector3:
    """A 3D vector in millimetres."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass(frozen=True)
class Quaternion:
    """A rotation quaternion (w, x, y, z).

    The identity quaternion is (1, 0, 0, 0).
    """

    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass(frozen=True)
class Transform:
    """A rigid transformation (rotation + translation).

    The identity transform is translation=(0,0,0) and
    rotation=(1,0,0,0).
    """

    translation: Vector3 = Vector3()
    rotation: Quaternion = Quaternion()

    @classmethod
    def identity(cls) -> Transform:
        return cls()

    def is_identity(self) -> bool:
        return self.translation == Vector3() and self.rotation == Quaternion()
