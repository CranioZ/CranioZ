"""Shared pytest fixtures for CranioZ tests."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Session-scoped QApplication.

    Creating multiple QApplication instances breaks Qt, so this fixture
    guarantees a single instance is reused across the entire test session.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app