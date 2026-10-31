"""Tests for InMemoryTransactionManager."""

from __future__ import annotations

import pytest

from cranioz.application.commands.transaction import (
    InMemoryTransactionManager,
    TransactionManager,
)


def test_satisfies_protocol() -> None:
    assert isinstance(InMemoryTransactionManager(), TransactionManager)


def test_commit_on_success() -> None:
    tm = InMemoryTransactionManager()
    with tm.begin():
        pass  # no exception → commit


def test_rollback_on_exception() -> None:
    tm = InMemoryTransactionManager()
    with pytest.raises(ValueError), tm.begin():
        raise ValueError("boom")
