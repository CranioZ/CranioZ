"""Debug script: render a synthetic Volume to isolate the adapter/reslice.

This script is a development tool. It is NOT part of production.

It creates a synthetic Volume with a known pattern (a cube with a
gradient along each axis) and renders three orthogonal slices
(axial, coronal, sagittal) in a native VTK window.

The pattern is:
  - Axial slice:   diagonal gradient (top-left to bottom-right).
  - Coronal slice: horizontal stripes.
  - Sagittal slice: vertical stripes.

If the pattern appears correctly, the VtkImageAdapter and
vtkImageReslice are correct, and the problem is the DICOM data
(slice ordering, orientation, direction matrix).
If the pattern appears with wrong orientation, the adapter or
reslice is broken.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_synthetic_volume.py

Run this DIRECTLY (not via pytest). Close the window to exit.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

import numpy as np
import vtk
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageReslice
from vtkmodules.vtkRenderingCore import (
    vtkImageActor,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from cranioz.domain.imaging.image_metadata import ImageMetadata
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.infrastructure.visualization.vtk_image_adapter import (
    VtkImageAdapter,
)

_SHAPE = (64, 64, 64)  # (nz, ny, nx)


def _make_synthetic_volume() -> Volume:
    nz, ny, nx = _SHAPE
    data = np.zeros((nz, ny, nx), dtype=np.int16)
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                # Each axis has a distinct pattern.
                data[k, j, i] = (i * 100) + (j * 10) + k
    geometry = VolumeGeometry.identity(
        dimensions=(nx, ny, nz),
        spacing=(1.0, 1.0, 1.0),
        origin=(0.0, 0.0, 0.0),
    )
    return Volume(
        data=data,
        geometry=geometry,
        metadata=ImageMetadata(),
        intensity_scale=IntensityScale.UNKNOWN,
        provenance=VolumeProvenance(
            import_timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        ),
        volume_id="synthetic",
    )


def _render_slice(volume: Volume, view_type: str, slice_index: int) -> None:
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)
    print(f"\n[{view_type}] vtkImageData dims: {image.GetDimensions()}")
    print(f"[{view_type}] vtkImageData range: {image.GetPointData().GetScalars().GetRange()}")

    reslice = vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()
    reslice.SetBackgroundLevel(0.0)

    dims = image.GetDimensions()
    spacing = image.GetSpacing()
    origin = image.GetOrigin()
    nx, ny, nz = dims

    if view_type == "axial":
        reslice.SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1)
        z = origin[2] + slice_index * spacing[2]
        reslice.SetResliceAxesOrigin(origin[0], origin[1], z)
    elif view_type == "coronal":
        reslice.SetResliceAxesDirectionCosines(1, 0, 0, 0, 0, 1, 0, -1, 0)
        y = origin[1] + slice_index * spacing[1]
        reslice.SetResliceAxesOrigin(origin[0], y, origin[2])
    elif view_type == "sagittal":
        reslice.SetResliceAxesDirectionCosines(0, 1, 0, 0, 0, 1, 1, 0, 0)
        x = origin[0] + slice_index * spacing[0]
        reslice.SetResliceAxesOrigin(x, origin[1], origin[2])
    else:
        raise ValueError(view_type)
    reslice.Update()

    slice_image = reslice.GetOutput()
    print(f"[{view_type}] slice dims: {slice_image.GetDimensions()}")
    print(f"[{view_type}] slice range: {slice_image.GetPointData().GetScalars().GetRange()}")

    wl = vtkImageMapToWindowLevelColors()
    wl.SetInputData(slice_image)
    wl.SetWindow(max(slice_image.GetPointData().GetScalars().GetRange()[1] -
                     slice_image.GetPointData().GetScalars().GetRange()[0], 1.0))
    wl.SetLevel((slice_image.GetPointData().GetScalars().GetRange()[0] +
                 slice_image.GetPointData().GetScalars().GetRange()[1]) / 2.0)
    wl.Update()

    actor = vtkImageActor()
    actor.GetMapper().SetInputConnection(wl.GetOutputPort())

    renderer = vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddActor(actor)

    render_window = vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(600, 600)
    render_window.SetWindowName(f"Synthetic {view_type} slice {slice_index}")
    render_window.SetMultiSamples(0)

    interactor = vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.Initialize()
    renderer.ResetCamera()
    render_window.Render()

    print(f"[{view_type}] Close the window to continue.")
    interactor.Start()


def main() -> int:
    volume = _make_synthetic_volume()
    print(f"Volume: dims={volume.dimensions}, spacing={volume.spacing}")
    print(f"Data range: ({volume.data.min()}, {volume.data.max()})")

    _render_slice(volume, "axial", 32)
    _render_slice(volume, "coronal", 32)
    _render_slice(volume, "sagittal", 32)

    print("\nAll slices rendered. Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())