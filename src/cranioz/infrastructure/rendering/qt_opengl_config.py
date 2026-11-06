"""Global Qt + VTK + OpenGL configuration.

This module MUST be imported before creating the QApplication and
before any VTK widget. It exists because PySide6 6.5+ defaults to
OpenGL Core Profile 3.2, while VTK 9's QVTKRenderWindowInteractor
still expects Compatibility Profile on Windows. Without this
configuration, VTK reports success but produces a silent white
widget (and, on some drivers, a 0xC0000005 crash).

The configuration is global, single, and idempotent. It lives in
the infrastructure layer because that is exactly what it is:
graphics infrastructure, not business rules, not use cases, not
widgets.
"""

from __future__ import annotations

import os

import vtk
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication


def configure_vtk_opengl() -> None:
    """Apply the global configuration. Idempotent.

    Must be called once, at the start of ``__main__``, before any
    ``QApplication`` or VTK widget is created.
    """
    # 1. Silence VTK's OpenGL warnings (they do not affect rendering).
    vtk.vtkObject.GlobalWarningDisplayOff()

    # 2. Force the Windows backend (prevents VTK from falling back to
    # OSMesa or another backend on machines with multiple drivers).
    os.environ.setdefault(
        "VTK_DEFAULT_OPENGL_WINDOW",
        "vtkWin32OpenGLRenderWindow",
    )

    # 3. Share the OpenGL context between Qt and VTK. Without this,
    # QVTKRenderWindowInteractor creates a separate context, invisible
    # to Qt, and the widget stays white.
    QApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts,
    )

    # 4. Force Compatibility Profile (OpenGL 2.1). PySide6 6.5+
    # defaults to Core Profile 3.2, which VTK 9 does not support on
    # Windows.
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setVersion(2, 1)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    QSurfaceFormat.setDefaultFormat(fmt)