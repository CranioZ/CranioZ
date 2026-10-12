"""CranioZ — Modular, open-source platform for virtual surgical planning in cranio-maxillofacial surgery.

This package exposes the public API of the CranioZ platform.
Internal modules should not be imported directly; use the entry points
and the public API defined here.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cranioz")
except PackageNotFoundError:  # running from source without installation
    __version__ = "0.0.0+local"

__author__ = "Jozeias Fernandes de Sousa"
__license__ = "AGPL-3.0-or-later"

__all__ = [
    "__version__",
    "__author__",
    "__license__",
]