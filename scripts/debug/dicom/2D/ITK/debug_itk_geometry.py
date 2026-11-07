"""Debug script: compare SimpleITK and current DicomSeriesReader geometry.

This script is a development tool. It is NOT part of production.

It does not render. It prints the geometry (dimensions, spacing, origin,
direction matrix, scalar range) produced by:
  1. SimpleITK.ImageSeriesReader (reference).
  2. The current DicomSeriesReader + VtkImageAdapter.

If the two geometries differ, the bug is in the current geometry
construction. If they match, the bug is in the VTK render pipeline.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_itk_geometry.py [path_to_dicom_folder]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (
    DicomSeriesReader,
    DicomSeriesReaderError,
)

try:
    import SimpleITK as sitk  # noqa: F401
except ImportError as exc:
    raise SystemExit(
        "SimpleITK is required for this debug script.\n"
        "Install it with: uv sync --extra debug-itk\n"
        f"(original error: {exc})"
    ) from exc


_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")


def _sitk_geometry(dicom_path: Path) -> dict:
    names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(str(dicom_path))
    if not names:
        raise RuntimeError(f"no DICOM series found in {dicom_path}")

    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(names)
    reader.SetOutputPixelType(sitk.sitkFloat32)
    image = reader.Execute()

    return {
        "size": image.GetSize(),
        "spacing": image.GetSpacing(),
        "origin": image.GetOrigin(),
        "direction": image.GetDirection(),
        "scalar_range": (
            float(np.asarray(image).min()),
            float(np.asarray(image).max()),
        ),
    }


def _current_geometry(dicom_path: Path) -> dict:
    reader = DicomSeriesReader()
    try:
        volume, _ = reader.read(dicom_path)
    except DicomSeriesReaderError as exc:
        raise RuntimeError(str(exc)) from exc

    return {
        "dimensions": volume.dimensions,
        "spacing": volume.spacing,
        "origin": volume.origin,
        "direction": tuple(tuple(row) for row in volume.geometry.direction),
        "scalar_range": volume.scalar_range,
    }


def _format_direction(d) -> str:
    return "; ".join(
        "(" + ", ".join(f"{v: .4f}" for v in row) + ")" for row in d
    )


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: debug_itk_geometry.py [path_to_dicom_folder]")
        return 1

    dicom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else _DEFAULT_DICOM_PATH
    if not dicom_path.is_dir():
        print(f"Not a directory: {dicom_path}")
        return 1

    print("=== SimpleITK geometry ===")
    try:
        itk = _sitk_geometry(dicom_path)
        print(f"  size: {itk['size']}")
        print(f"  spacing: {itk['spacing']}")
        print(f"  origin: {itk['origin']}")
        print(f"  direction: 9-tuple {itk['direction']}")
        print(f"  scalar range: {itk['scalar_range']}")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        itk = None

    print("\n=== Current DicomSeriesReader geometry ===")
    try:
        cur = _current_geometry(dicom_path)
        print(f"  dims: {cur['dimensions']}")
        print(f"  spacing: {cur['spacing']}")
        print(f"  origin: {cur['origin']}")
        print(f"  direction: {_format_direction(cur['direction'])}")
        print(f"  scalar range: {cur['scalar_range']}")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        cur = None

    if itk is not None and cur is not None:
        print("\n=== Comparison ===")
        same_dims = tuple(itk["size"]) == tuple(cur["dimensions"])
        same_spacing = np.allclose(itk["spacing"], cur["spacing"], atol=1e-4)
        same_origin = np.allclose(itk["origin"], cur["origin"], atol=1e-2)
        itk_dir = np.array(itk["direction"]).reshape(3, 3)
        cur_dir = np.array(cur["direction"])
        same_direction = np.allclose(itk_dir, cur_dir, atol=1e-4)

        print(f"  dimensions match: {same_dims}")
        print(f"  spacing match:    {same_spacing}")
        print(f"  origin match:     {same_origin}")
        print(f"  direction match:  {same_direction}")

        if not all((same_dims, same_spacing, same_origin, same_direction)):
            print("\n  >>> Geometry differs. The bug is in the current")
            print("  >>> Volume/VolumeGeometry construction.")
        else:
            print("\n  >>> Geometry matches. The bug is in the VTK render")
            print("  >>> pipeline (reslice, camera, transfer functions).")

    return 0


if __name__ == "__main__":
    sys.exit(main())