"""CoordinateSystem — enumeration of supported coordinate conventions.

The CranioZ domain uses **RAS** internally (Right, Anterior, Superior),
which is the convention used by NIfTI, ITK, and most visualization
pipelines.

DICOM uses **LPS** (Left, Posterior, Superior). The conversion between
LPS and RAS is an explicit reflection (two axis inversions), and must
occur at the infrastructure boundary (DICOM reader), never silently
in the domain.

IJK represents voxel index coordinates (i, j, k), which are not a
physical coordinate system but are useful for referring to the
geometry model.

See Medical Imaging Infrastructure §5.2.
"""

from __future__ import annotations

from enum import Enum


class CoordinateSystem(Enum):
    """Supported coordinate conventions."""

    RAS = "ras"
    """Right, Anterior, Superior. Internal CranioZ convention."""

    LPS = "lps"
    """Left, Posterior, Superior. DICOM convention."""

    IJK = "ijk"
    """Voxel index coordinates (i, j, k). Not a physical system."""
