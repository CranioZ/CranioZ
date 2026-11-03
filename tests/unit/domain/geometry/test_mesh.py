"""Tests for Mesh."""

from __future__ import annotations

import numpy as np
import pytest

from cranioz.domain.geometry.coordinate_frame import CoordinateFrame
from cranioz.domain.geometry.mesh import Mesh, MeshError


def _frame() -> CoordinateFrame:
    return CoordinateFrame.identity()


def _triangle_vertices() -> np.ndarray:
    return np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        dtype=np.float32,
    )


def _triangle_faces() -> np.ndarray:
    return np.array([[0, 1, 2]], dtype=np.uint32)


def _make_mesh(**overrides) -> Mesh:
    kwargs = {
        "vertices": _triangle_vertices(),
        "faces": _triangle_faces(),
        "coordinate_frame": _frame(),
    }
    kwargs.update(overrides)
    return Mesh(**kwargs)


# ----- Construction ------------------------------------------------


def test_minimal_mesh_is_accepted() -> None:
    mesh = _make_mesh()
    assert mesh.vertex_count == 3
    assert mesh.face_count == 1
    assert mesh.vertices.dtype == np.float32
    assert mesh.faces.dtype == np.uint32


def test_float64_vertices_are_accepted() -> None:
    mesh = _make_mesh(vertices=_triangle_vertices().astype(np.float64))
    assert mesh.vertices.dtype == np.float64


def test_uint64_faces_are_accepted() -> None:
    mesh = _make_mesh(faces=_triangle_faces().astype(np.uint64))
    assert mesh.faces.dtype == np.uint64


# ----- Invariants --------------------------------------------------


def test_vertices_must_be_2d() -> None:
    with pytest.raises(MeshError, match="must have shape \\(N, 3\\)"):
        _make_mesh(vertices=np.zeros((3,), dtype=np.float32))


def test_vertices_must_have_three_columns() -> None:
    with pytest.raises(MeshError, match="must have shape \\(N, 3\\)"):
        _make_mesh(vertices=np.zeros((3, 2), dtype=np.float32))


def test_vertices_dtype_must_be_supported() -> None:
    with pytest.raises(MeshError, match="dtype must be one of"):
        _make_mesh(vertices=np.zeros((3, 3), dtype=np.int32))


def test_vertices_must_be_finite() -> None:
    bad = _triangle_vertices()
    bad[0, 0] = float("nan")
    with pytest.raises(MeshError, match="must be finite"):
        _make_mesh(vertices=bad)


def test_empty_vertices_raise() -> None:
    with pytest.raises(MeshError, match="at least one vertex"):
        _make_mesh(vertices=np.zeros((0, 3), dtype=np.float32))


def test_faces_must_be_2d() -> None:
    with pytest.raises(MeshError, match="must have shape \\(M, 3\\)"):
        _make_mesh(faces=np.zeros((3,), dtype=np.uint32))


def test_faces_must_have_three_columns() -> None:
    with pytest.raises(MeshError, match="must have shape \\(M, 3\\)"):
        _make_mesh(faces=np.zeros((1, 4), dtype=np.uint32))


def test_faces_dtype_must_be_supported() -> None:
    with pytest.raises(MeshError, match="dtype must be one of"):
        _make_mesh(faces=np.zeros((1, 3), dtype=np.int32))


def test_faces_must_reference_existing_vertices() -> None:
    bad_faces = np.array([[0, 1, 99]], dtype=np.uint32)
    with pytest.raises(MeshError, match="reference vertex index"):
        _make_mesh(faces=bad_faces)


def test_empty_faces_raise() -> None:
    with pytest.raises(MeshError, match="at least one face"):
        _make_mesh(faces=np.zeros((0, 3), dtype=np.uint32))


# ----- Immutability ------------------------------------------------


def test_vertices_are_read_only_after_construction() -> None:
    mesh = _make_mesh()
    with pytest.raises(ValueError, match="read-only"):
        mesh.vertices[0, 0] = 99.0


def test_faces_are_read_only_after_construction() -> None:
    mesh = _make_mesh()
    with pytest.raises(ValueError, match="read-only"):
        mesh.faces[0, 0] = 99


def test_mesh_is_frozen() -> None:
    mesh = _make_mesh()
    with pytest.raises(AttributeError):
        mesh.vertices = _triangle_vertices()  # type: ignore[misc]


# ----- Representation ---------------------------------------------


def test_repr_contains_key_information() -> None:
    mesh = _make_mesh()
    text = repr(mesh)
    assert "vertices=3" in text
    assert "faces=1" in text
    assert "float32" in text
    assert "uint32" in text
