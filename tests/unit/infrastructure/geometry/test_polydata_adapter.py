"""Tests for the Mesh → vtkPolyData adapter."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("vtk")

from cranioz.domain.geometry.coordinate_frame import CoordinateFrame
from cranioz.domain.geometry.mesh import Mesh
from cranioz.infrastructure.geometry.adapters.vtk.polydata import (
    mesh_to_polydata,
)


def _triangle_mesh() -> Mesh:
    return Mesh(
        vertices=np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            dtype=np.float32,
        ),
        faces=np.array([[0, 1, 2]], dtype=np.uint32),
        coordinate_frame=CoordinateFrame.identity(),
    )


def test_conversion_preserves_vertex_count() -> None:
    mesh = _triangle_mesh()
    poly = mesh_to_polydata(mesh)
    assert poly.GetNumberOfPoints() == mesh.vertex_count


def test_conversion_preserves_cell_count() -> None:
    mesh = _triangle_mesh()
    poly = mesh_to_polydata(mesh)
    assert poly.GetNumberOfCells() == mesh.face_count


def test_conversion_preserves_coordinates() -> None:
    mesh = _triangle_mesh()
    poly = mesh_to_polydata(mesh)
    points = poly.GetPoints()
    assert points is not None
    coords = np.array([points.GetPoint(i) for i in range(points.GetNumberOfPoints())])
    np.testing.assert_allclose(coords, mesh.vertices, atol=1e-6)


def test_float64_vertices_are_accepted() -> None:
    mesh = Mesh(
        vertices=np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            dtype=np.float64,
        ),
        faces=np.array([[0, 1, 2]], dtype=np.uint32),
        coordinate_frame=CoordinateFrame.identity(),
    )
    poly = mesh_to_polydata(mesh)
    assert poly.GetNumberOfPoints() == 3
