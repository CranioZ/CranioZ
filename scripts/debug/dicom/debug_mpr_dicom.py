"""Debug script: load a DICOM series and display it in an isolated MPRView.

This script is a development tool. It is NOT part of production.

It bypasses the Workspace, TomographyEditor, and Scene entirely. It loads
a DICOM series, builds a Volume, and displays it in a single MPRView
(axial). This isolates the DICOM -> Volume -> VtkImageAdapter -> MPRView
pipeline.

The MPRView now has:
  - A locked display plane (no pan/zoom/rotation).
  - A slider at the bottom to navigate between slices.
  - Direction-aware reslicing (respects the volume's direction matrix).

Usage:

    .venv\\Scripts\\python.exe scripts\\debug\\dicom\\debug_mpr_dicom.py [path_to_dicom_folder]

If no path is given, it defaults to the path below. Close the window to exit.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow

from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (
    DicomSeriesReader,
    DicomSeriesReaderError,
)
from cranioz.ui.editors.mpr_viewer.view import MPRView

#: Default DICOM folder for manual debugging. Override via the command line.
_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: debug_mpr_dicom.py [path_to_dicom_folder]")
        return 1

    dicom_path = Path(sys.argv[1]) if len(sys.argv) == 2 else _DEFAULT_DICOM_PATH
    if not dicom_path.is_dir():
        print(f"Not a directory: {dicom_path}")
        return 1

    print(f"Loading DICOM series from {dicom_path}...")
    reader = DicomSeriesReader()
    try:
        volume, report = reader.read(dicom_path)
    except DicomSeriesReaderError as exc:
        print(f"Failed to load DICOM: {exc}")
        return 1

    print(f"Volume loaded: dims={volume.dimensions}, spacing={volume.spacing}")
    print(f"Intensity scale: {volume.intensity_scale.value}")
    print(f"Report: {report.summary()}")

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")

    view = MPRView(view_id="view.axial", view_type="axial")
    view.set_volume(volume)

    window = QMainWindow()
    window.setWindowTitle("CranioZ - MPR Debug (Axial)")
    window.setCentralWidget(view.content_widget())
    window.resize(800, 800)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())