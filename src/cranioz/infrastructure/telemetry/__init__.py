"""Telemetry infrastructure — adapters for the TelemetrySink protocol.

The application core depends on ``cranioz.application.telemetry``
(the Protocol). This package provides the concrete adapters:

- ``LoggingTelemetrySink`` — writes to the standard logging framework.
- ``NoOpTelemetrySink`` — discards everything (re-exported from the
  application layer for convenience).
"""

from cranioz.application.telemetry.noop_sink import NoOpTelemetrySink
from cranioz.infrastructure.telemetry.logging_sink import LoggingTelemetrySink

__all__ = [
    "LoggingTelemetrySink",
    "NoOpTelemetrySink",
]
