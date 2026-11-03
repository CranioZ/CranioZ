"""Geometry I/O — file format readers and writers.

The initial implementation supports STL. Additional formats are
introduced only when a concrete clinical requirement justifies them.
"""

from cranioz.infrastructure.geometry.io.stl import read_stl, write_stl

__all__ = ["read_stl", "write_stl"]
