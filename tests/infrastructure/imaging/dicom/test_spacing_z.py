from __future__ import annotations

import os
from pathlib import Path

import pytest

from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (
    DicomSeriesReader,
)

_DEFAULT_DICOM_PATH = Path(r"C:\Users\JozeiasNote2026\Downloads\TC")
_DICOM_PATH = Path(os.environ.get("CRANIOZ_TEST_DICOM_PATH", _DEFAULT_DICOM_PATH))


@pytest.mark.skipif(
    not _DICOM_PATH.is_dir(),
    reason=(
        "Dataset de referência não disponível. "
        "Defina CRANIOZ_TEST_DICOM_PATH ou coloque um dataset em "
        f"{_DEFAULT_DICOM_PATH}."
    ),
)
def test_spacing_z_from_image_position_patient() -> None:
    """O spacing_z deve ser a distância real entre ImagePositionPatient.

    O dataset de referência tem spacing de ~0.2 mm em Z. Se o valor
    estiver próximo de 0.5, 1.0 ou de qualquer SliceThickness declarado
    no DICOM, o código está usando a fonte errada.
    """
    reader = DicomSeriesReader()
    volume, _ = reader.read(_DICOM_PATH)

    assert 0.19 < volume.spacing[2] < 0.21, (
        f"spacing_z={volume.spacing[2]}. Esperado ~0.2 mm. "
        f"Se estiver próximo de 0.5 ou 1.0, o código está usando "
        f"SliceThickness em vez de ImagePositionPatient."
    )
