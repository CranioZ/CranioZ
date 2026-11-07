from __future__ import annotations

from datetime import UTC, datetime

import numpy as np

from cranioz.domain.imaging.image_metadata import ImageMetadata
from cranioz.domain.imaging.volume import IntensityScale, Volume
from cranioz.domain.imaging.volume_geometry import VolumeGeometry
from cranioz.domain.imaging.volume_provenance import VolumeProvenance
from cranioz.infrastructure.visualization.vtk_image_adapter import VtkImageAdapter


def _make_asymmetric_volume() -> Volume:
    """Cria um Volume sintético com padrão assimétrico (X, Y, Z distintos)."""
    nz, ny, nx = 8, 6, 4
    data = np.zeros((nz, ny, nx), dtype=np.int16)
    for z in range(nz):
        for y in range(ny):
            for x in range(nx):
                data[z, y, x] = x * 100 + y * 10 + z

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
        volume_id="test-ordering",
    )


def test_voxel_ordering_matches_numpy() -> None:
    """Garante que cada voxel do vtkImageData corresponde ao Volume.data.

    Este teste é o guardião da correção do bug histórico: a combinação
    de transpose(2,1,0) com ravel(order='C') corrompia o layout de memória
    e produzia artefatos de listras na renderização 3D.
    """
    volume = _make_asymmetric_volume()
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)

    nx, ny, nz = volume.dimensions

    corners = [
        (0, 0, 0),
        (nx - 1, 0, 0),
        (0, ny - 1, 0),
        (0, 0, nz - 1),
        (nx - 1, ny - 1, nz - 1),
        (nx // 2, ny // 2, nz // 2),
    ]

    for i, j, k in corners:
        vtk_value = image.GetScalarComponentAsFloat(i, j, k, 0)
        numpy_value = float(volume.data[k, j, i])
        assert vtk_value == numpy_value, (
            f"Mismatch em (i={i}, j={j}, k={k}): "
            f"vtkImageData={vtk_value}, Volume.data={numpy_value}. "
            f"Suspeita de reintrodução do bug de transposição."
        )


def test_voxel_ordering_matches_numpy_everywhere() -> None:
    """Verifica TODOS os voxels, não apenas os cantos.

    Isso garante que nenhuma permutação parcial de eixos esteja ocorrendo.
    """
    volume = _make_asymmetric_volume()
    adapter = VtkImageAdapter()
    image = adapter.to_vtk(volume)

    nx, ny, nz = volume.dimensions

    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                vtk_value = image.GetScalarComponentAsFloat(i, j, k, 0)
                numpy_value = float(volume.data[k, j, i])
                assert vtk_value == numpy_value, (
                    f"Mismatch em (i={i}, j={j}, k={k}): "
                    f"vtkImageData={vtk_value}, Volume.data={numpy_value}."
                )
