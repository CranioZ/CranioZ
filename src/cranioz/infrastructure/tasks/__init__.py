"""Task infrastructure — Qt-backed TaskManager (ADR-0011).

The ``QtTaskManager`` is the production implementation of the
``TaskManager`` Protocol defined in ``cranioz.application.tasks.base``.

The package has a hard dependency on PySide6 (QThreadPool, QObject,
QMetaObject), which is expected: the TaskManager exists to bridge the
GUI thread and worker threads in a Qt application.
"""

from cranioz.infrastructure.tasks.qt_task_manager import QtTaskManager

__all__ = ["QtTaskManager"]
