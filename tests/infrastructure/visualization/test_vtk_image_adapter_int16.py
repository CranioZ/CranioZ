from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import vtk

from cranioz.domain.imaging.image_metadata import ImageMetadata
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.infrastructure.visualization.vtk_image_adapter import VtkImageAdapter


def _make_volume_with_range(min_value: int, max_value: int) -> Volume:
    """Cria um Volume pequeno com range conhecido para teste de fidelidade."""
    nz, ny, nx = 4, 4, 4
    data = np.linspace(min_value, max_value, nz * ny * nx, dtype=np.int16).reshape((nz, ny, nx))

    return Volume(
        data=data,
        geometry=VolumeGeometry.identity(
            dimensions=(nx, ny, nz),
            spacing=(1.0, 1.0, 1.0),
            origin=(0.0, 0.0, 0.0),
        ),
        metadata=ImageMetadata(),
        intensity_scale=IntensityScale.UNKNOWN,
        provenance=VolumeProvenance(import_timestamp=datetime.now(UTC)),
        volume_id="test-int16",
    )


def test_int16_preserves_scalar_range() -> None:
    """O range do vtkImageData deve ser idêntico ao do Volume.data.

    Esta é a garantia de fidelidade clínica: os valores não podem ser
    normalizados nem truncados, sob pena de perda de informação em HU.
    """
    volume = _make_volume_with_range(min_value=-1000, max_value=3000)
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)

    scalars = image.GetPointData().GetScalars()
    assert scalars is not None

    vtk_min, vtk_max = scalars.GetRange()
    np_min = float(volume.data.min())
    np_max = float(volume.data.max())

    assert vtk_min == np_min, f"Mínimo divergente: vtkImageData={vtk_min}, Volume.data={np_min}."
    assert vtk_max == np_max, f"Máximo divergente: vtkImageData={vtk_max}, Volume.data={np_max}."


def test_int16_preserves_dtype() -> None:
    """O tipo escalar do vtkImageData deve ser VTK_SHORT (int16).

    A conversão para uint8 deve ser evitada em produção: o benchmark
    de 2026-11-06 confirmou que int16 é 17x mais rápido na conversão
    e 81% mais rápido na renderização, além de preservar a fidelidade.
    """
    volume = _make_volume_with_range(min_value=-1000, max_value=3000)
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)

    scalars = image.GetPointData().GetScalars()
    assert scalars is not None
    assert scalars.GetDataType() == vtk.VTK_SHORT, (
        f"Tipo escalar inesperado: {scalars.GetDataTypeAsString()}. Esperado VTK_SHORT (int16)."
    )


def test_int16_negative_values_are_preserved() -> None:
    """Valores negativos (ar, tecido mole) devem sobreviver à conversão.

    Alguns volumes CBCT têm range de -6114 a 16383. Se o adapter
    convertesse para uint8 sem normalização, os negativos virariam zero
    e a janela de transferência perderia informação.
    """
    volume = _make_volume_with_range(min_value=-6114, max_value=16383)
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)

    scalars = image.GetPointData().GetScalars()
    assert scalars is not None

    # Encontrar um voxel com valor negativo no Volume.data
    negative_indices = np.argwhere(volume.data < 0)
    assert len(negative_indices) > 0, "O volume de teste não tem valores negativos."

    k, j, i = negative_indices[0]
    vtk_value = image.GetScalarComponentAsFloat(int(i), int(j), int(k), 0)
    numpy_value = float(volume.data[k, j, i])

    assert vtk_value == numpy_value, (
        f"Valor negativo perdido em (i={i}, j={j}, k={k}): "
        f"vtkImageData={vtk_value}, Volume.data={numpy_value}."
    )
