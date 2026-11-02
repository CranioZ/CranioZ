"""Tests for DicomValidator."""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.infrastructure.imaging.dicom.dicom_validator import (
    DicomValidator,
)

# ----- Helpers ------------------------------------------------------


@dataclass
class FakeFileMeta:
    TransferSyntaxUID: str = "1.2.840.10008.1.2.1"


@dataclass
class FakeDataset:
    Rows: int = 4
    Columns: int = 4
    BitsAllocated: int = 16
    BitsStored: int = 16
    PixelRepresentation: int = 1
    ImagePositionPatient: list[float] | None = None
    ImageOrientationPatient: list[float] | None = None
    PixelSpacing: list[float] | None = None
    file_meta: FakeFileMeta | None = None

    def __post_init__(self) -> None:
        if self.ImagePositionPatient is None:
            self.ImagePositionPatient = [0.0, 0.0, 0.0]
        if self.ImageOrientationPatient is None:
            self.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        if self.PixelSpacing is None:
            self.PixelSpacing = [1.0, 1.0]
        if self.file_meta is None:
            self.file_meta = FakeFileMeta()


def _make_slice(z: float = 0.0) -> FakeDataset:
    return FakeDataset(ImagePositionPatient=[0.0, 0.0, z])


# ----- Minimum slices ----------------------------------------------


def test_too_few_slices() -> None:
    validator = DicomValidator()
    result = validator.validate([_make_slice(0.0)])
    assert result.has_errors
    assert any(i.code == "too_few_slices" for i in result.issues)


def test_enough_slices() -> None:
    validator = DicomValidator()
    result = validator.validate([_make_slice(0.0), _make_slice(1.0)])
    assert not result.has_errors


# ----- Dimensions ---------------------------------------------------


def test_inconsistent_dimensions() -> None:
    validator = DicomValidator()
    s1 = FakeDataset(ImagePositionPatient=[0.0, 0.0, 0.0], Rows=4, Columns=4)
    s2 = FakeDataset(ImagePositionPatient=[0.0, 0.0, 1.0], Rows=5, Columns=4)
    result = validator.validate([s1, s2])
    assert any(i.code == "inconsistent_dimensions" for i in result.issues)


# ----- Pixel spacing -----------------------------------------------


def test_inconsistent_pixel_spacing_warning() -> None:
    validator = DicomValidator()
    s1 = FakeDataset(ImagePositionPatient=[0.0, 0.0, 0.0], PixelSpacing=[1.0, 1.0])
    s2 = FakeDataset(ImagePositionPatient=[0.0, 0.0, 1.0], PixelSpacing=[0.5, 0.5])
    result = validator.validate([s1, s2])
    assert any(i.code == "inconsistent_pixel_spacing" for i in result.issues)


# ----- Transfer syntax ---------------------------------------------


def test_unsupported_transfer_syntax() -> None:
    validator = DicomValidator()
    s1 = FakeDataset(
        ImagePositionPatient=[0.0, 0.0, 0.0],
        file_meta=FakeFileMeta(TransferSyntaxUID="1.2.840.10008.1.2.4.50"),
    )
    s2 = FakeDataset(ImagePositionPatient=[0.0, 0.0, 1.0])
    result = validator.validate([s1, s2])
    assert any(i.code == "unsupported_transfer_syntax" for i in result.issues)


# ----- Irregular slice spacing -------------------------------------


def test_irregular_spacing_warning() -> None:
    validator = DicomValidator()
    slices = [
        FakeDataset(ImagePositionPatient=[0.0, 0.0, 0.0]),
        FakeDataset(ImagePositionPatient=[0.0, 0.0, 1.0]),
        FakeDataset(ImagePositionPatient=[0.0, 0.0, 2.0]),
        FakeDataset(ImagePositionPatient=[0.0, 0.0, 4.0]),
    ]
    result = validator.validate(slices)
    assert any(i.code == "irregular_slice_spacing" for i in result.issues)
