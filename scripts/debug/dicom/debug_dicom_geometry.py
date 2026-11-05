"""Debug script: inspect the DICOM geometry (orientation, direction, origin).

This script is a development tool. It is NOT part of production.

It reads the DICOM series, then prints:
  - ImageOrientationPatient (first slice).
  - ImagePositionPatient (first and last slice).
  - PixelSpacing, Rows, Columns.
  - The direction matrix computed by DicomSorter.
  - The origin computed by DicomSorter.
  - Whether the direction is identity (which the VtkImageAdapter
    assumes).

If the direction is not identity, the VtkImageAdapter must either
apply it (via SetDirectionMatrix) or reorient the volume to identity.
The current VtkImageAdapter does neither, which causes the MPR reslice
to cut the volume in the wrong plane.

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_dicom_geometry.py [path_to_dicom_folder]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from cranioz.infrastructure.imaging.dicom.dicom_sorter import DicomSorter
from cranioz.infrastructure.imaging.dicom.dicom_validator import DicomValidator

_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: debug_dicom_geometry.py [path_to_dicom_folder]")
        return 1
    dicom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else _DEFAULT_DICOM_PATH
    if not dicom_path.is_dir():
        print(f"Not a directory: {dicom_path}")
        return 1

    import pydicom

    print(f"Reading DICOM from {dicom_path}...")
    files = sorted(p for p in dicom_path.iterdir() if p.is_file())
    slices = []
    for f in files:
        try:
            ds = pydicom.dcmread(str(f), force=False)
        except Exception:
            continue
        if hasattr(ds, "PixelData"):
            slices.append(ds)
    print(f"Loaded {len(slices)} image slices.")

    first = slices[0]
    last = slices[-1]
    print("\n--- First slice ---")
    print(f"  Modality: {getattr(first, 'Modality', None)}")
    print(f"  Rows x Columns: {first.Rows} x {first.Columns}")
    print(f"  PixelSpacing: {getattr(first, 'PixelSpacing', None)}")
    print(f"  SliceThickness: {getattr(first, 'SliceThickness', None)}")
    print(f"  ImagePositionPatient: {getattr(first, 'ImagePositionPatient', None)}")
    print(f"  ImageOrientationPatient: {getattr(first, 'ImageOrientationPatient', None)}")
    print(f"  InstanceNumber: {getattr(first, 'InstanceNumber', None)}")

    print("\n--- Last slice ---")
    print(f"  ImagePositionPatient: {getattr(last, 'ImagePositionPatient', None)}")
    print(f"  InstanceNumber: {getattr(last, 'InstanceNumber', None)}")

    print("\n--- Sorter ---")
    sorter = DicomSorter()
    sorted_slices, direction_ras = sorter.sort(slices)
    print(f"  Sorted {len(sorted_slices)} slices.")
    print(f"  direction_ras:\n{direction_ras}")

    is_identity = np.allclose(direction_ras, np.eye(3), atol=1e-6)
    print(f"  is_identity: {is_identity}")

    if not is_identity:
        det = np.linalg.det(direction_ras)
        print(f"  determinant: {det:.6f}")
        print("  The direction is NOT identity. This is the bug:")
        print("  - VtkImageAdapter ignores the direction matrix.")
        print("  - vtkImageReslice uses fixed axes (identity), so it")
        print("    cuts the volume in a plane that is wrong relative to")
        print("    the patient's anatomy.")
        print("  Fix options:")
        print("    A) Apply SetDirectionMatrix on the vtkImageData.")
        print("    B) Reorient the Volume to identity in the adapter.")
        print("    C) Set the reslice axes from the direction matrix.")

    print("\n--- Validator ---")
    validator = DicomValidator()
    result = validator.validate(slices)
    for issue in result.issues:
        print(f"  [{issue.severity.value}] {issue.code}: {issue.message}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())