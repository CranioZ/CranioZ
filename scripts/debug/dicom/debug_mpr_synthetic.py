"""Debug script: test the MPRView with a synthetic Volume.

This script is a development tool. It is NOT part of production.

It creates a synthetic Volume (gradient) and displays it in the real
MPRView. If the gradient appears, the MPRView is correct and the
problem is the DICOM data. If the gradient does not appear, the
problem is the MPRView (specifically the vtkImageActor + W/L + interactor
style).

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_mpr_synthetic.py

Run this DIRECTLY (not via pytest). Close the window to exit.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow

from cranioz.domain.imaging.image_metadata import ImageMetadata
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.ui.editors.mpr_viewer.view import MPRView


def _make_synthetic_volume() -> Volume:
    nz, ny, nx = 64, 64, 64
    data = np.zeros((nz, ny, nx), dtype=np.int16)
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
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


def main() -> int:
    volume = _make_synthetic_volume()
    print(f"Synthetic Volume: dims={volume.dimensions}")
    print(f"Data range: ({volume.data.min()}, {volume.data.max()})")

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    view = MPRView(view_id="view.axial", view_type="axial")
    view.set_volume(volume)

    window = QMainWindow()
    window.setWindowTitle("CranioZ - MPR Synthetic (Axial)")
    window.setCentralWidget(view.content_widget())
    window.resize(800, 800)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())