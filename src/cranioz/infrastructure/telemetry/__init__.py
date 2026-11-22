"""Telemetry infrastructure — adapters for the TelemetrySink protocol.

The main_window core depends on ``cranioz.main_window.telemetry``
(the Protocol). This package provides the concrete adapters:

- ``LoggingTelemetrySink`` — writes to the standard logging framework.
- ``NoOpTelemetrySink`` — discards everything (re-exported from the
  main_window layer for convenience).
"""

from cranioz.application.telemetry.noop_sink import NoOpTelemetrySink
from cranioz.infrastructure.telemetry.logging_sink import LoggingTelemetrySink

__all__ = [
    "LoggingTelemetrySink",
    "NoOpTelemetrySink",
]
