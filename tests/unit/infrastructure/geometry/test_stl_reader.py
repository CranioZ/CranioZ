"""Tests for the STL reader and writer."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

pytest.importorskip("vtk")

from cranioz.domain.geometry.coordinate_frame import CoordinateFrame
from cranioz.infrastructure.geometry.io.stl import (
    StlReadError,
    read_stl,
    write_stl,
)


def _write_triangle_stl(path: Path, scale: float = 1.0) -> None:
    """Write a single-triangle binary STL, for tests only."""
    header = b"\x00" * 80
    body = struct.pack("<I", 1)
    triangle = (
        struct.pack("<3f", 0.0, 0.0, 1.0)
        + struct.pack("<3f", 0.0 * scale, 0.0 * scale, 0.0 * scale)
        + struct.pack("<3f", 1.0 * scale, 0.0 * scale, 0.0 * scale)
        + struct.pack("<3f", 0.0 * scale, 1.0 * scale, 0.0 * scale)
        + struct.pack("<H", 0)
    )
    path.write_bytes(header + body + triangle)


def test_reads_single_triangle(tmp_path: Path) -> None:
    stl_path = tmp_path / "triangle.stl"
    _write_triangle_stl(stl_path)

    mesh = read_stl(stl_path)

    assert mesh.vertex_count == 3
    assert mesh.face_count == 1
    assert mesh.vertices.dtype == __import__("numpy").float32
    assert mesh.faces.dtype == __import__("numpy").uint32
    assert mesh.coordinate_frame.name == "RAS"


def test_unit_scale_is_applied(tmp_path: Path) -> None:
    stl_path = tmp_path / "triangle.stl"
    _write_triangle_stl(stl_path, scale=10.0)

    mesh = read_stl(stl_path, unit_scale=0.1)

    # The STL has coordinates at 10mm; scaling by 0.1 converts to 1mm.
    max_coord = float(mesh.vertices.max())
    assert max_coord == pytest.approx(1.0, abs=1e-5)


def test_custom_coordinate_frame_is_recorded(tmp_path: Path) -> None:
    stl_path = tmp_path / "triangle.stl"
    _write_triangle_stl(stl_path)
    frame = CoordinateFrame(name="custom", origin=(1.0, 2.0, 3.0))

    mesh = read_stl(stl_path, coordinate_frame=frame)

    assert mesh.coordinate_frame is frame


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(StlReadError, match="not found"):
        read_stl(tmp_path / "does_not_exist.stl")


def test_invalid_unit_scale_raises(tmp_path: Path) -> None:
    stl_path = tmp_path / "triangle.stl"
    _write_triangle_stl(stl_path)
    with pytest.raises(StlReadError, match="unit_scale"):
        read_stl(stl_path, unit_scale=0.0)


def test_round_trip_preserves_topology(tmp_path: Path) -> None:
    stl_path = tmp_path / "triangle.stl"
    _write_triangle_stl(stl_path)
    original = read_stl(stl_path)

    out_path = tmp_path / "roundtrip.stl"
    write_stl(original, out_path)
    reread = read_stl(out_path)

    assert reread.vertex_count == original.vertex_count
    assert reread.face_count == original.face_count
