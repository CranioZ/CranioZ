"""TransactionManager — transaction boundary for Commands (ADR-0007).

A Command maps to exactly one transaction (ADR-0007 §2.3). The
CommandExecutor opens a transaction, calls the Handler, and commits
or rolls back. The Handler is unaware of the transaction.

For the first version, the in-memory transaction manager is a no-op
(commands are applied synchronously; a failed Handler raises, and the
executor does not publish events). A future version may use a
unit-of-work that captures and restores Scene state.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol, runtime_checkable

_logger = logging.getLogger(__name__)


@runtime_checkable
class TransactionManager(Protocol):
    """Opens and manages transactions for Command execution."""

    @contextmanager
    def begin(self) -> Iterator[None]: ...


class InMemoryTransactionManager:
    """Reference implementation of ``TransactionManager``.

    The transaction is a no-op: ``commit`` and ``rollback`` only log.
    The CommandExecutor is responsible for not publishing events if
    the Handler raises (it never calls ``commit``).
    """

    @contextmanager
    def begin(self) -> Iterator[None]:
        """Context manager that logs commit/rollback."""
        _logger.debug("transaction: begin")
        try:
            yield
        except Exception:
            _logger.debug("transaction: rollback (handler raised)")
            raise
        else:
            _logger.debug("transaction: commit")
