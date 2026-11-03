"""Geometry adapters — bridges between canonical geometry and concrete backends.

The initial adapter targets VTK, the documented backend for geometry
processing and visualization (§10 of the Geometry Infrastructure
document). The adapter does not mutate the canonical ``Mesh``; it
only reads its read-only arrays.
"""
