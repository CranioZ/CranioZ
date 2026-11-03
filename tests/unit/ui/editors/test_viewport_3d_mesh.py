"""Tests for Viewport3DView.set_mesh (STL validation helper)."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

pytest.importorskip("vtk")
pytest.importorskip("vtkmodules.qt")

from cranioz.infrastructure.geometry.io.stl import read_stl
from cranioz.ui.editors.viewport_3d.view import Viewport3DView


def _write_minimal_stl(path: Path) -> None:
    """Write a single-triangle binary STL, for tests only."""
    header = b"\x00" * 80
    body = struct.pack("<I", 1)
    triangle = (
        struct.pack("<3f", 0.0, 0.0, 1.0)
        + struct.pack("<3f", 0.0, 0.0, 0.0)
        + struct.pack("<3f", 1.0, 0.0, 0.0)
        + struct.pack("<3f", 0.0, 1.0, 0.0)
        + struct.pack("<H", 0)
    )
    path.write_bytes(header + body + triangle)


@pytest.mark.qt
def test_set_mesh_adds_actor(qtbot, tmp_path: Path) -> None:
    stl_path = tmp_path / "triangle.stl"
    _write_minimal_stl(stl_path)
    mesh = read_stl(stl_path)

    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())

    view.set_mesh(mesh)

    assert view.has_mesh is True
    assert view.mesh is mesh
    assert view.renderer is not None
    props = view.renderer.GetViewProps()
    assert props.GetNumberOfItems() >= 1


@pytest.mark.qt
def test_set_mesh_replaces_previous(qtbot, tmp_path: Path) -> None:
    stl_a = tmp_path / "a.stl"
    stl_b = tmp_path / "b.stl"
    _write_minimal_stl(stl_a)
    _write_minimal_stl(stl_b)
    mesh_a = read_stl(stl_a)
    mesh_b = read_stl(stl_b)

    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())

    view.set_mesh(mesh_a)
    view.set_mesh(mesh_b)

    assert view.mesh is mesh_b


@pytest.mark.qt
def test_set_mesh_none_raises(qtbot) -> None:
    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())

    with pytest.raises(ValueError, match="non-None Mesh"):
        view.set_mesh(None)  # type: ignore[arg-type]


@pytest.mark.qt
def test_dispose_clears_mesh_state(qtbot, tmp_path: Path) -> None:
    stl_path = tmp_path / "triangle.stl"
    _write_minimal_stl(stl_path)
    mesh = read_stl(stl_path)

    view = Viewport3DView(view_id="view.3d")
    qtbot.addWidget(view.content_widget())
    view.set_mesh(mesh)
    assert view.has_mesh is True

    view.dispose()

    assert view.has_mesh is False
    assert view.mesh is None
