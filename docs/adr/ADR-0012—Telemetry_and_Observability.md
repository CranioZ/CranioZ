# ADR-0012: Telemetry and Observability

**Status:** Accepted
**Date:** 2026-10-22
**Deciders:** Architecture team
**Related:** modules.md §6.1, §15; overview.md §20; implementation.md §6.4; ADR-0011

---

## 1. Context

CranioZ is a clinical application. Failures and performance regressions
have direct consequences for surgeons and patients: a slow DICOM import
delays a planning session, a silent error in an osteotomy computation
can produce a wrong plan, and an unlogged activation failure can leave
a workspace in an unknown state. The application must be observable
without becoming a monitoring platform.

Three concerns must be distinguished:

- **Logging** — structured records of what happened, for debugging
  and post-mortem analysis. Already partially defined (logging YAML,
  `logging.getLogger`).
- **Telemetry** — measurements of duration, counts, and outcomes, for
  performance analysis and capacity planning.
- **Auditability** — records of *who did what*, for regulatory and
  clinical compliance (out of scope here; covered by `project.md` §28).

Without a unified observability model, each module, editor, or service
invents its own logging format, its own metric names, and its own
correlation IDs. Cross-component diagnostics become impossible, and
performance regressions are invisible until a clinician reports them.

This ADR defines the telemetry contract: a `TelemetrySink` protocol,
the event taxonomy, the correlation model, and the boundary between
the application core and its adapters. It is the counterpart of
ADR-0011 for measurement, in the same way ADR-0011 defines the
counterpart for threading.

## 2. Decision

### 2.1 Two levels: structured events and measurements

The telemetry system has exactly two data types:

- **Event** — a structured record of a discrete occurrence:
  "module loaded", "command failed", "task cancelled". Events carry a
  name, a timestamp, a correlation id, a severity, and a payload
  (free-form key-value attributes).
- **Measurement** — a numerical observation of a duration, count, or
  gauge: "module load took 142 ms", "segmentation processed 500
  slices", "RAM used 1.8 GB". Measurements carry a name, a value, a
  unit, a timestamp, a correlation id, and optional attributes.

Nothing else. Traces are a composition of events and measurements
with the same correlation id. Spans are not a first-class concept;
they are derived by the adapter that materializes the data (e.g., a
future OpenTelemetry exporter).

### 2.2 TelemetrySink contract

```python
class TelemetrySink(Protocol):
    def record_event(
        self,
        name: str,
        *,
        severity: Severity = Severity.INFO,
        attributes: Mapping[str, Any] | None = None,
    ) -> None: ...

    def record_measurement(
        self,
        name: str,
        value: float,
        *,
        unit: MeasurementUnit = MeasurementUnit.NONE,
        attributes: Mapping[str, Any] | None = None,
    ) -> None: ...


class Severity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MeasurementUnit(Enum):
    NONE = "none"
    MILLISECONDS = "ms"
    SECONDS = "s"
    BYTES = "bytes"
    COUNT = "count"
    PERCENT = "percent"
```
The contract is deliberately minimal. A TelemetrySink does not
provide span context, tracing propagation, or aggregation; those are
adapter concerns. The sink records data; the adapter decides where
the data goes (log file, metrics file, network exporter, test buffer).

2.3 Correlation
Every event and measurement carries a correlation_id: a string
generated when a user-facing operation begins (a module load, an
activation, a command dispatch, a task dispatch) and propagated to
every event and measurement produced during that operation.

The application core generates the correlation_id at the entry
point of each operation and passes it down. Components do not
generate their own; a component that needs a correlation id receives
it explicitly, either as a parameter or through a scoped context.

The correlation id is the only tracing mechanism. There is no
"parent span id", no "trace id", no "baggage". When a future
OpenTelemetry adapter is introduced, it derives the span structure
from the sequence of events with the same correlation id.

2.4 Event taxonomy
Event names are dot-separated, lowercase, stable, and independent of
the user-facing text. The taxonomy is open: components may record
custom events, but the following names are reserved by the
application core:

Name	Producer	Attributes
app.start	__main__	version, os, python
app.stop	__main__	uptime_ms
module.load.start	ModuleLoader	module_id
module.load.success	ModuleLoader	module_id, duration_ms
module.load.failure	ModuleLoader	module_id, error_type
module.unload.start	ModuleLoader	module_id
module.unload.success	ModuleLoader	module_id, duration_ms
module.unload.failure	ModuleLoader	module_id, error_type
module.activate	Application layer	module_id, spec_name
module.deactivate	Application layer	module_id
workspace.load_spec	Workspace	area_count
command.dispatch	CommandBus	command_type
command.success	CommandBus	command_type, duration_ms
command.failure	CommandBus	command_type, error_type
task.dispatch	TaskManager	task_name
task.complete	TaskManager	task_name, duration_ms
task.cancel	TaskManager	task_name, reason
task.failure	TaskManager	task_name, error_type
Component-specific events (e.g., segmentation.threshold.applied,
cephalometry.landmark.verified) are added by their producers. They
follow the same naming convention and carry the same correlation id.

2.5 Measurement taxonomy
Measurement names follow the same dot-separated convention.
Reserved names:

Name	Unit	Producer
module.load.duration	milliseconds	ModuleLoader
module.unload.duration	milliseconds	ModuleLoader
workspace.load_spec.duration	milliseconds	Workspace
command.dispatch.duration	milliseconds	CommandBus
task.duration	milliseconds	TaskManager
app.memory.rss	bytes	__main__ (periodic)
app.gui.fps	count	future
Component-specific measurements (e.g.,
segmentation.slices.processed) are added by their producers.

2.6 Severity mapping
Severity is orthogonal to the event name. The producer chooses the
severity of each event; the adapter maps it to the underlying
mechanism (e.g., WARNING and above → WARNING log; INFO →
INFO log; DEBUG → DEBUG log, disabled by default outside
development).

A command.failure event is ERROR. A command.success event is
INFO. A task.cancel event is INFO. A module.load.failure
event is ERROR if the load was triggered by a user action and
WARNING if the load was speculative. Producers are responsible for
choosing the severity that matches the operational impact.

2.7 Adapters
The TelemetrySink Protocol is implemented by adapters:

NoOpTelemetrySink — discards everything. Default for tests
and for the early application before a real adapter is configured.

LoggingTelemetrySink — writes events and measurements to the
standard logging framework. Measurements are logged as
name=value unit attributes={...} at DEBUG level by default.
This is the default adapter for development and for the first
release.

FileTelemetrySink — writes newline-delimited JSON to a file.
Intended for support bundles and clinical study data. The file
location is resolved by AppPathResolver.

Future: OTelTelemetrySink — exports to an OpenTelemetry
collector. The Protocol is compatible with OTel spans; the adapter
derives spans from sequences of events with the same
correlation_id.

The adapter is chosen at boot by __main__ based on configuration
(config/defaults/telemetry.json). The application core never
imports an adapter; it receives a TelemetrySink instance.

2.8 Injection
The TelemetrySink is a shared application service. It is injected
at __main__ into the MainWindow, which injects it into the
Workspace, which exposes it via Workspace.telemetry_sink(). It is
also injected into each ModuleContext and EditorContext, so
components do not import the application core.

Components receive the sink as a constructor parameter or through
their context; they never call a global get_telemetry_sink(). The
global accessor exists only in __main__ for wiring.

2.9 Testability
The NoOpTelemetrySink is the default in test fixtures. Tests that
verify telemetry behavior use an in-memory RecordingTelemetrySink
that captures events and measurements in lists, so they can assert
on names, severities, and attributes without parsing logs.

A test that needs to verify that a component emits a specific event
injects the recording sink and asserts on the captured data. The
application core does not need a "telemetry is enabled" flag; the
sink is the flag.

2.10 Non-goals
Auditability. Recording who did what for regulatory purposes
is a separate concern (project.md §28) with its own storage, access
controls, and retention policy. The telemetry system may carry an
actor attribute, but it does not implement audit semantics.

Clinical event tracking. Clinical outcomes (e.g., "osteotomy
verified by surgeon") are domain events, not telemetry. They go
through the EventBus and the CommandBus, not the TelemetrySink.

Alerting. The application does not evaluate alerts. A future
deployment may feed the adapter into an external alerting system;
the application core does not.

PII. Telemetry does not carry patient-identifying information.
Attributes must not include names, dates of birth, patient IDs, or
image paths. Components are responsible for respecting this rule;
the adapter does not redact.

3. Rationale
3.1 Why a Protocol and not a concrete class
A TelemetrySink implementation depends on the deployment (log
file, OTel collector, study database). A Protocol lets the
application core depend on the abstraction, while __main__ chooses
the adapter. This is the same pattern as ProjectRepository,
EventBus, and TaskManager.

3.2 Why correlation id and not spans
Spans require a tracing exporter and a propagation model. CranioZ
does not have one yet, and adding one would lock the domain to a
specific tracing backend. The correlation id is a plain string that
any adapter can interpret: the logging adapter groups by it, the
file adapter groups by it, and a future OTel adapter derives spans
from it.

3.3 Why events and measurements are separate
A measurement has a numeric value and a unit; an event has a
severity and a payload. Merging them would force events to carry a
value or measurements to carry a severity, both of which are
misleading. Keeping them separate lets adapters handle them
differently (measurements to a metric backend, events to a log
backend) without coupling.

3.4 Why the adapter does not redact PII
The application core knows which fields are patient-identifying; a
generic adapter does not. Redaction in the adapter would be either
incomplete (it cannot see all paths) or fragile (it depends on
attribute names). The rule is: components do not emit PII in
telemetry. A future audit of attribute names can be enforced by the
TelemetryValidator (future piece).

3.5 Why the sink is injected and not global
A global get_telemetry_sink() would hide the dependency and make
tests that need a recording sink fragile (they would have to
configure the global and reset it). Injection makes the dependency
explicit and lets each test own its sink.

4. Consequences
4.1 Positive
One event and measurement taxonomy for the application.

Correlation across components without a tracing backend.

Adapters are swappable (NoOp, Logging, File, future OTel).

Tests can assert on telemetry without parsing logs.

The application core does not know where telemetry goes.

4.2 Negative
Every component that emits telemetry must accept a sink. This is
one more constructor parameter (or one more ModuleContext /
EditorContext field).

PII safety is a discipline, not an enforced invariant. A future
TelemetryValidator can enforce it, but the first version does
not.

A NoOp sink in production would hide everything. The
configuration must choose a real adapter; the default at boot is
LoggingTelemetrySink.

4.3 Neutral
Spans are not first-class. This is deliberate and can be revisited
when the project needs a real tracing backend.

The taxonomy is open. Components can add events and measurements
without changing the application core.

5. Rules applied by this ADR
Every telemetry emission is an event or a measurement.

Every event and measurement carries a correlation_id.

The application core generates the correlation_id at the entry
point of each operation and passes it down.

The TelemetrySink Protocol has two methods: record_event and
record_measurement.

Event names are dot-separated, lowercase, stable, and reserved by
the application core (see §2.4) or by the component (with the
same convention).

Measurement names follow the same convention.

The adapter is chosen at __main__ and injected into
MainWindow, Workspace, ModuleContext, and EditorContext.

Components do not call a global get_telemetry_sink(). The
global accessor exists only in __main__ for wiring.

The NoOpTelemetrySink is the default in tests. The
LoggingTelemetrySink is the default in development.

PII (names, dates of birth, patient IDs, image paths) is not
emitted as telemetry attributes.

Clinical events and audit records are not telemetry. They use
the EventBus and the CommandBus.

6. Rejected alternatives
6.1 Python's logging alone
Rejected. logging handles events but not measurements, and it does
not provide a correlation id. Adding measurements to logging
records (e.g., logger.info("duration=%d", ms)) would require
parsing logs for metrics, which is fragile and slow.

6.2 A global metrics module
Rejected. A global module hides the dependency and makes tests
fragile. Injection is the same pattern as EventBus, TaskManager,
and ProjectRepository.

6.3 OpenTelemetry from day one
Rejected. OTel is a heavy dependency with its own SDK, exporter,
and configuration. The TelemetrySink Protocol is compatible with
OTel spans (derived from sequences of events), so a future
OTelTelemetrySink can be introduced without changing the
application core.

6.4 Emitting telemetry from a decorator
Rejected. A decorator (e.g., @measured) would hide the emission
site and make it hard to add context (correlation id, attributes
specific to the operation). Explicit sink.record_event(...) calls
are verbose but clear.

6.5 Redacting PII in the adapter
Rejected. The adapter does not know which attributes are
patient-identifying. Redaction would be either incomplete or
fragile. The rule is: components do not emit PII.

6.6 Merging events and measurements
Rejected. Events carry severity and a payload; measurements carry
a numeric value and a unit. Merging them would force one to carry
the other's fields, which is misleading. Adapters handle them
differently.

7. Summary
The TelemetrySink is the single boundary between CranioZ and its
observability backend. It records events and measurements, both
carrying a correlation_id, and nothing else. The application core
depends on the Protocol; __main__ chooses the adapter
(NoOp, Logging, File, future OTel). Components receive the
sink by injection; they do not import a global. PII, audit records,
and clinical events are out of scope.

The contract is deliberately small: record_event,
record_measurement, Severity, MeasurementUnit, and a
correlation_id. The adapter is free to translate these into logs,
metrics, spans, or files; the application core does not care.