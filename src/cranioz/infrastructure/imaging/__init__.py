"""DICOM infrastructure — reading, validation, calibration, assembly.

This package handles single-frame CT/CBCT DICOM series. It is the
implementation of the Medical Imaging Infrastructure contracts for
DICOM.

It does NOT depend on VTK. The conversion to `vtkImageData` happens
later, in `infrastructure/visualization/vtk_image_adapter.py`.

See Medical Imaging Infrastructure §5, §7.
"""

from cranioz.infrastructure.imaging.dicom.dicom_calibrator import (
    DicomCalibrator,
)
from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (
    DicomSeriesReader,
    DicomSeriesReaderError,
)
from cranioz.infrastructure.imaging.dicom.dicom_sorter import (
    DicomSorter,
    DicomSorterError,
)
from cranioz.infrastructure.imaging.dicom.dicom_validator import (
    DicomValidator,
    ValidationResult,
)

__all__ = [
    "DicomCalibrator",
    "DicomSeriesReader",
    "DicomSeriesReaderError",
    "DicomSorter",
    "DicomSorterError",
    "DicomValidator",
    "ValidationResult",
]
