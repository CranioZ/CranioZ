"""Visualization infrastructure — adapters from domain to rendering.

This package bridges the domain `Volume` to the VTK rendering layer.
It does NOT contain rendering logic (actors, mappers, cameras). It
only converts data representations.

See Medical Imaging Infrastructure §12 (Visualization Integration).
"""

from cranioz.infrastructure.visualization.vtk_image_adapter import (
    VtkImageAdapter,
)

__all__ = ["VtkImageAdapter"]
