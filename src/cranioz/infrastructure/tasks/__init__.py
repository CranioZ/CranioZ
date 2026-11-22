"""Task infrastructure — Qt-backed TaskManager (ADR-0011).

The ``QtTaskManager`` is the production implementation of the
``TaskManager`` Protocol defined in ``cranioz.main_window.tasks.base``.

The package has a hard dependency on PySide6 (QThreadPool, QObject,
QMetaObject), which is expected: the TaskManager exists to bridge the
GUI thread and worker threads in a Qt main_window.
"""

from cranioz.infrastructure.tasks.qt_task_manager import QtTaskManager

__all__ = ["QtTaskManager"]
