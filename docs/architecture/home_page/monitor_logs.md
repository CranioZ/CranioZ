# Logs Monitor

**Document type:** Technical specification
**Status:** Planned (not implemented)
**Scope:** Developer/support diagnostic window fed by `logging`
**Last updated:** 2026-11-22

---

## 1. Purpose and scope

The Logs Monitor is the developer-facing diagnostic window of CranioZ. It
presents application logging records grouped by subsystem in a single
non-modal floating window, accessible from the HomePage top bar.

It helps developers and support personnel understand:

- What happened during application startup?
- Which component produced an error or warning?
- What is the current Workspace Area layout state?
- Which subsystem is generating excessive log output?
- What happened during an asynchronous operation?

The Logs Monitor is **not**:

- A user-facing console (see §2).
- A clinical operation history or undo stack (see §2).
- A telemetry channel (see §2).
- A replacement for the log file or stdout (see §6.6).

The specification is complete, but implementation is pending. The
`logs_requested` signal is reserved in `home_page.md` §25. The Workspace
layout snapshot contract (§7) is not yet implemented.

This document is the single source of truth for the implementation.

---

## 2. Audience and separation of channels

CranioZ exposes three distinct communication channels. They must remain
independent.

| Channel | Audience | Content | Host | Data source |
|---|---|---|---|---|
| **Console** | Clinical user | Operational messages, warnings, errors and progress from the platform and running Flow. | `ConsoleEditor` (Bottom Area, declared by a Module). | Application-level notification service (to be defined). |
| **History** | Clinical user | Chronological sequence of user operations, including Undo/Redo. | `HistoryEditor` (Bottom Area, declared by a Module). | Application command history. |
| **Logs Monitor** | Developer / support | DEBUG, INFO, WARNING, ERROR and CRITICAL records, stack traces, layout snapshots and diagnostic information. | Floating window opened from the HomePage top bar. | Dedicated `logging.Handler`. |

The Console is not fed directly by `logging`. Mixing the channels would
expose clinical users to developer-only messages, including Qt warnings,
library diagnostics and internal implementation details.

The Console is an application communication channel. The Logs Monitor is
a technical diagnostic channel.

This separation is a project invariant.

A single application event may produce both a user-facing notification and
a technical log record, but each must use its own communication mechanism
and appropriate content.

---

## 3. Architectural role

The Logs Monitor belongs to the UI layer.

It:

- Observes application logging records.
- Routes records to subsystem tabs.
- Displays formatted diagnostic information.
- Provides copy and exit controls.

It does not:

- Read the log file from disk (§10).
- Know the internal structure of the Workspace, Scene, ProjectIndex,
  EventBus, Editors, Modules or domain.
- Participate in clinical undo/redo.
- Modify application state.
- Generate telemetry.
- Configure or manage logging handlers.

It depends on:

- `QtLogHandler`, responsible for receiving, formatting, routing and
  buffering records.
- `TranslationService`, for the HomePage button tooltip and any
  translated UI labels inside the window.
- `IconProvider`, for the window icon and the HomePage button icon.

The Logs Monitor is a read-only observer. Its UI state is limited to
presentation state, including the contents and scroll positions of its
tabs.

---

## 4. Non-responsibilities

The Logs Monitor does not:

- Configure logging (bootstrap responsibility, §8).
- Install or remove handlers.
- Change logger levels or filtering rules.
- Parse diagnostic information beyond displaying formatted records.
- Persist records across process restarts.
- Reorder, deduplicate or aggregate records.
- Provide interactive log-level filtering.
- Replace or duplicate the log file.
- Interact with `TelemetrySink`, `EventBus`, `CommandBus` or Application
  services.
- Provide clinical data validation or clinical workflow functionality.

The Monitor displays information produced by the application. It does not
determine whether an operation or clinical result is correct.

---

## 5. The `LogsDialog` widget

### 5.1 Window type and identity

- Class: `LogsDialog`.
- Location: `cranioz/ui/diagnostics/logs_dialog.py`.
- Base class: `QDialog`.
- Window flags: `Qt.WindowType.Tool`.
- Modality: Non-modal.
- Title: `CranioZ — Logs Monitor`. **Fixed, not translated.** The product
  name and the diagnostic-window name are stable identifiers; translating
  them would create ambiguity in screenshots, support tickets and issue
  reports.
- HomePage button tooltip: `Logs`. **Translated** through
  `TranslationService` (key `home.toolbar.logs` in `en/` and `pt-BR/`).
  The button itself is the 📋 icon provided by `IconProvider`.
- Ownership: One instance per `MainWindow`.
- Repeated requests raise and activate the existing instance.
- Closing the dialog hides it instead of destroying it.
- Its contents remain available until `MainWindow` is destroyed.

The asymmetry between the fixed window title and the translated tooltip is
intentional: the title is a stable technical label, the tooltip is a
user-facing affordance.

### 5.2 Layout and tabs

```text
LogsDialog
├── QTabWidget
│   ├── Boot
│   ├── Home Page
│   ├── Workspace
│   ├── Areas
│   ├── Scene
│   ├── Project
│   ├── Tomography
│   └── Segmentation (reserved)
└── QHBoxLayout
    ├── QPushButton "Copy Log"
    └── QPushButton "Exit"
```

Each tab contains a `QPlainTextEdit` configured as follows:

- `setReadOnly(True)`.
- Platform-default monospace font.
- `QPlainTextEdit.LineWrapMode.NoWrap`.
- Maximum block count of 5,000.
- Automatic scrolling to the bottom when new records arrive, unless the
  user has scrolled away from the bottom.

The `Segmentation` tab is reserved for future use. It remains empty until
its corresponding subsystem is implemented (Phase 6A).

Tab order is defined centrally and must remain stable.

### 5.3 Tab-to-logger mapping

Routing is based on `record.name`, using exact logger prefixes delimited
by dots.

| Tab | Logger prefixes |
|---|---|
| `Boot` | `cranioz.__main__`, `cranioz.config` |
| `Home Page` | `cranioz.ui.home` |
| `Workspace` | `cranioz.ui.workspace` (excluding tagged layout snapshots) |
| `Areas` | `cranioz.ui.workspace` (tagged layout snapshots only) |
| `Scene` | `cranioz.application.scene`, `cranioz.domain.scene` |
| `Project` | `cranioz.application.project` |
| `Tomography` | `cranioz.editors.builtin.tomography` |
| `Segmentation` | `cranioz.application.segmentation` (**provisional**) |
| `General` | Fallback for unclassified records |

`General` is the fallback tab. Unknown loggers must not be routed to
`Boot`, since their origin may have no relationship with application
startup.

**Provisional routing for `Segmentation`.** The package
`cranioz.application.segmentation` does not exist yet. The prefix above
is the planned name; it will be confirmed when the segmentation subsystem
is introduced in Phase 6A. Until then, no records are expected to reach
the `Segmentation` tab, and the tab remains empty. This is a deliberate
placeholder, not a routing defect.

The mapping is defined in a module-level constant:

```python
TAB_ROUTES: tuple[tuple[str, str], ...]
```

The routing implementation must use boundary-aware prefix matching. For
example, `cranioz.ui.home.page` matches `cranioz.ui.home`, but
`cranioz.ui.homepage` does not.

The `Areas` and `Workspace` tabs share a logger prefix. They are
distinguished by the structured `area_snapshot` record attribute (§7).

### 5.4 Copy Log and Exit

**Copy Log**

- Copies the complete text of the currently active tab.
- Includes a trailing newline when the content is non-empty.
- Does not copy other tabs.
- Does not include the tab title.
- Uses the system clipboard.

If clipboard access fails, the operation must fail safely without
affecting the application.

**Exit**

- Hides the dialog.
- Does not close the application.
- Does not affect `MainWindow`.
- Does not stop logging or clear buffered records.

### 5.5 Lifecycle and wiring

`MainWindow` owns the single `LogsDialog` instance.

```python
# MainWindow.__init__
self._logs_dialog: LogsDialog | None = None

# MainWindow._on_logs_requested
if self._logs_dialog is None:
    self._logs_dialog = LogsDialog(
        log_handler=self._log_handler,
        translation_service=self._translation_service,
        icon_provider=self._icon_provider,
        parent=self,
    )

self._logs_dialog.show()
self._logs_dialog.raise_()
self._logs_dialog.activateWindow()
```

`MainWindow` receives the `QtLogHandler` instance from bootstrap. The
dialog never installs or removes logging handlers.

The dialog is destroyed with `MainWindow` through Qt parent ownership.

The handler remains owned by bootstrap and is removed during application
shutdown (§8).

**Precondition on `logs_requested`.** The `LogsDialog` is never created
before the `QtLogHandler` is installed. If `logs_requested` fires while
`self._log_handler is None` (a bootstrap-ordering defect), the request is
ignored and a warning is logged. This is a defensive check, not a normal
path.

### 5.6 Initial content synchronization

The dialog must display records produced before its first opening.

The handler owns the record buffer. The dialog does not access its
internal storage directly.

**Timing.** Initial synchronization is performed on the **first
`show()`**, not in `__init__`. The dialog is shown empty first, then
populated from the snapshot. This avoids blocking the constructor with a
potentially large snapshot (up to 8 tabs × 5,000 entries) while the user
is waiting for the window to appear. The populated content is visible
within the same event-loop turn as the `show()` call, so the user does
not perceive an intermediate empty state.

Sequence:

1. Connect the dialog to the handler's record signal.
2. Request an atomic snapshot of the buffered records.
3. Populate the corresponding tabs.
4. Ignore queued records whose sequence numbers are already included in
   the snapshot.

Each `LogEntry` has a monotonically increasing sequence number assigned by
the handler.

The snapshot operation returns the buffered entries and the corresponding
sequence watermark under the same synchronization lock.

This prevents missing or duplicating records when the dialog is
initialized while logging is active.

Subsequent records are delivered through Qt signals.

---

## 6. The `QtLogHandler`

### 6.1 Responsibility

`QtLogHandler` is a `logging.Handler` integrated with Qt's signal/slot
mechanism.

It is the only bridge between Python logging and the Logs Monitor.

Its responsibilities are:

- Receive `LogRecord` instances.
- Format records.
- Determine their destination tab.
- Create immutable `LogEntry` objects.
- Store records in bounded per-tab buffers.
- Notify the UI when new records arrive.

It does not format records for the file or stdout handlers.

### 6.2 Log entry representation

Records are converted into an immutable representation before being stored
or forwarded.

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    sequence: int
    timestamp: str
    level: int
    logger_name: str
    tab: str
    message: str
```

The `message` field contains the formatted message, including exception
and stack information when available.

The original `LogRecord` is not retained by the UI.

### 6.3 Record routing

For each record, the handler:

1. Reads `record.name`.
2. Resolves the destination using `TAB_ROUTES`.
3. Checks `record.area_snapshot` when the logger belongs to the
   Workspace.
4. Uses `General` when no route matches.
5. Formats the record.
6. Creates a `LogEntry`.
7. Appends the entry to the corresponding buffer.
8. Emits the record notification signal.

Routing must be deterministic and stateless.

The handler must not reorder records.

**Inconsistent tag.** If `record.area_snapshot` is `True` and
`record.name` does **not** start with `cranioz.ui.workspace`, the record
is routed to `General` and a single warning is emitted for the offending
logger name (deduplicated per logger, to avoid a warning storm). This is
a programming error in the producing subsystem, not a user-facing
condition.

### 6.4 Threading and GUI-thread marshalling

Logging may occur from any application thread, including background Tasks.

The handler must never manipulate `QWidget` instances or other GUI objects
from a worker thread.

Implementation:

- `QtLogHandler` integrates `logging.Handler` and `QObject`.
- It exposes a Qt signal carrying a `LogEntry`.
- The signal is emitted from the thread producing the record.
- The dialog receives the signal through a queued connection.
- UI updates execute exclusively on the GUI thread.

The handler uses a thread lock to protect sequence assignment and buffer
operations.

The lock must not be held while performing GUI operations or waiting for
UI acknowledgment.

The handler must use explicit initialization for both base classes and
must not create or manipulate widgets.

**Relationship to `TaskManager`.** The `QtLogHandler` is a marshalling
mechanism, not a work-execution mechanism. It does **not** create threads,
`QThread`, `ThreadPoolExecutor`, `ProcessPoolExecutor`, `asyncio` loops,
or raw threads. The "TaskManager is the only application mechanism for
off-thread work" rule (`implementation_plan.md` §7.4, ADR-0011) remains
intact.

### 6.5 Formatting

The default format is:

```text
HH:MM:SS LEVEL  logger_name: message
```

Example:

```text
14:32:08 INFO     cranioz.application.scene: Scene initialized
14:32:09 WARNING  cranioz.application.project: Missing optional metadata
14:32:11 ERROR    cranioz.editors.tomography: Failed to load volume
```

Formatting requirements:

- Timestamp uses the record creation time, displayed to seconds.
- Level name is right-aligned to a width of 8 characters.
- Logger name is `record.name`.
- Message is obtained through `record.getMessage()`.

Use `logging.Formatter` for standard formatting and exception handling.

The formatter must include:

- `record.exc_info`, when available.
- `record.stack_info`, when available.

Multiline messages and tracebacks are preserved.

Continuation lines are displayed without repeating the timestamp and
logger prefix.

The format is defined once in a module-level constant:

```python
LINE_FORMAT: str
```

The timestamp is generated through the formatter, not by assuming that
`record.asctime` already exists.

### 6.6 Interaction with existing handlers

The `QtLogHandler` is additive.

It does not replace:

- File handler.
- Stdout handler.
- `LoggingTelemetrySink`.

Each handler receives records independently according to its logger and
handler configuration.

The Qt handler uses:

```python
self.setLevel(logging.DEBUG)
```

However, its level alone does not guarantee that DEBUG records reach it.
The originating logger must also allow those records to be created.

Subsystems requiring diagnostic DEBUG records must explicitly configure
their logger level without unnecessarily lowering the root logger's
level.

For example, the Workspace logger may use DEBUG while the application
root remains at INFO.

The file and stdout handlers retain their own configured levels.

### 6.7 Buffer management

The handler maintains a separate bounded buffer for each tab.

Initial configuration:

| Property | Value |
|---|---|
| Buffer type | FIFO |
| Maximum entries | 5,000 per tab |
| Overflow policy | Remove oldest entries |
| Persistence | In-memory only |
| Synchronization | Thread lock |

The buffer is implemented using bounded collections, such as
`collections.deque(maxlen=5000)`.

The dialog's `QPlainTextEdit` uses the same maximum block count.

The handler buffer is the authoritative in-memory record store. The
dialog is a presentation copy.

### 6.8 High-volume logging

The handler must avoid unnecessary GUI updates during bursts of records.

Record reception and buffering must remain immediate, but UI notification
may be batched when several records arrive in rapid succession.

Batching must preserve sequence order and must not block logging threads.

The initial implementation should remain simple. A more sophisticated
batching mechanism is only justified if testing demonstrates GUI event
queue congestion.

---

## 7. The `Areas` tab — Workspace layout contract

### 7.1 Purpose

The `Areas` tab provides a chronological diagnostic record of applied
Workspace layouts.

It is a textual history of layout events, not a live representation of
the current Workspace state.

The Workspace emits two kinds of records:

- One aggregated INFO record per applied layout.
- One DEBUG record per Area in that layout.

These records describe Area-level structural state only.

### 7.2 Logged information

Allowed fields:

- `area_id`
- `placement`
- `visible`
- `size`
- Number of Editors
- Layout shape
- Root dimensions
- Region bounds
- Layout sequence identifier

Example:

```text
layout applied id=12 areas=3 visible=[central]
sizes=[0,960,0] root=1200x800
regions={central:1200x800,left:placeholder,right:placeholder,bottom:placeholder}
```

Per-Area records:

```text
area.central placement=central visible=True size=1200x800 editors=2 layout=SPLIT(H)
area.left placement=left visible=False size=0x0 editors=1 layout=LEAF
```

### 7.3 Levels and frequency

| Level | Frequency | Content |
|---|---|---|
| INFO | Once per applied layout | Aggregated layout information |
| DEBUG | Once per Area per applied layout | Individual Area information |

The existing INFO message in `Workspace._compute_vertical_sizes` describing
splitter calculations must be lowered to DEBUG when this contract is
implemented.

The purpose is to avoid multiple INFO records for a single layout
application.

### 7.4 Routing tag

Layout snapshot records use a structured logging attribute:

```python
extra = {"area_snapshot": True}
```

The handler routes records carrying this attribute to the `Areas` tab.

Other records from `cranioz.ui.workspace` go to the `Workspace` tab.

The formatted message remains the information displayed to the user. The
structured attribute is used exclusively for routing.

### 7.5 Emission point

The aggregated INFO record is emitted at the end of
`Workspace._apply_default_splitter_sizes`, after the splitter sizes have
been applied and before the deferred overlay repositioning call.

Per-Area DEBUG records are emitted in the same block.

The snapshot must reflect the actual applied result, not an intermediate
`LayoutTree` configuration.

All records belonging to the same layout application must share the same
layout sequence identifier.

The Workspace must not emit snapshots from unrelated locations.

Layout changes that do not pass through this operation are logged as
ordinary Workspace records, if applicable.

### 7.6 Logging restrictions

The Areas tab must not contain:

- Editor identifiers or internal Editor state.
- Tool or Toolbar names.
- Scene identifiers.
- Clinical object identifiers.
- Project identifiers or names.
- Patient names.
- File paths containing clinical identifiers.
- Telemetry-shaped records.

The tab describes Workspace structure, not clinical content.

### 7.7 Environment-dependent clinical data policy

Clinical information in diagnostic logs is governed by the application's
logging environment.

**Environment determination.** The environment is determined by the
logging configuration, for example `logging.environment:
development | testing | production` in `app.json`. It is resolved by
`_configure_logging` **before any handler is installed**, so that every
handler — file, stdout, telemetry and Qt — observes the same policy from
the first record. The Logs Monitor does not read the environment; it
receives records whose PHI policy has already been applied by the
producing subsystem or by a configured `logging.Filter`.

**Development.** During development, diagnostic logs may contain clinical
information when necessary for implementation, debugging and validation
using clinical datasets. This includes information required to
investigate data loading, image geometry, segmentation, measurements and
other clinical processing operations. Access to development logs and
datasets must remain controlled.

**Testing.** Testing environments may use clinical information according
to the dataset and validation requirements. Public, simulated or
anonymized datasets should be preferred whenever they are sufficient.

**Production.** Production logging must not expose identifiable clinical
information. The production logging configuration must apply the
appropriate sanitization and exclusion policies before records reach
diagnostic and persistent handlers. This includes:

- Patient names and identifiers.
- Study and series identifiers.
- Clinical file paths.
- DICOM identifying metadata.
- Other patient-identifiable information.
- Exception messages containing clinical input data.

The policy must be applied centrally during logging configuration, not
implemented exclusively in the Qt handler.

All handlers, including file, stdout, telemetry and Qt handlers, must
respect the configured environment policy.

The Logs Monitor must not be treated as an exception to production data
protection requirements.

---

## 8. Bootstrap wiring

### 8.1 Handler creation and installation

The `QtLogHandler` is created in `cranioz.__main__`, inside `main()`.

It is installed after `_configure_logging(config)` and before `MainWindow`
construction.

```python
handler = QtLogHandler()

logging.getLogger().addHandler(handler)
```

The instance is passed to `MainWindow` as a keyword argument alongside
`task_manager` and `telemetry`.

The bootstrap owns the handler throughout the application lifecycle.

### 8.2 Configuration ordering

`_configure_logging(config)` runs before the Qt handler is installed.

This ensures that the file and stdout handlers are already configured.

The Qt handler is additive and independent of those handlers.

Records emitted before handler installation are not captured by the Logs
Monitor.

These early records remain subject to the existing bootstrap logging
configuration.

The application must not claim that the Monitor captures records emitted
before its handler is installed.

### 8.3 Shutdown

The handler is removed from the root logger during application shutdown.

The shutdown sequence must prevent records from being delivered to a GUI
event loop that has already stopped.

The proposed sequence is:

```python
exit_code = app.exec()

logging.getLogger().removeHandler(handler)
task_manager.shutdown()
```

The handler is removed before TaskManager shutdown.

This prevents shutdown-time background records from being delivered to an
inactive UI.

The handler is owned and removed by bootstrap, never by `LogsDialog`.

The handler should be closed after removal when its lifecycle is
complete.

---

## 9. Error handling and failure modes

| Failure | Behavior |
|---|---|
| A record cannot be delivered because the dialog is hidden or not yet created. | The record remains in the handler buffer. |
| The dialog is destroyed while records are being produced. | No widget access occurs from the handler. Buffered records remain available until handler shutdown. |
| The clipboard is unavailable. | Copy operation fails safely without affecting the application. |
| A record has no recognizable logger prefix. | Routed to `General`. |
| A record carries `area_snapshot=True`. | Routed to `Areas`. |
| A record carries `area_snapshot=True` but its logger is not under `cranioz.ui.workspace`. | Routed to `General`; a warning is logged once per offending logger. |
| A buffer reaches its maximum capacity. | Oldest records are discarded according to FIFO policy. |
| The UI receives duplicate queued records during initial synchronization. | Sequence numbers prevent duplicate presentation. |
| A worker thread emits a logging record. | Record is buffered safely and delivered through a queued Qt connection. |
| A logger has `propagate=False`. | Its records are not captured by the root handler unless it has another applicable handler. |
| Logging is reconfigured after handler installation. | The logging configuration must preserve the handler registration and expected logger propagation behavior. |
| The application runs with production data protection enabled. | Clinical identifying information is sanitized or excluded before reaching handlers. |
| `logs_requested` fires before the handler is installed. | Request ignored; a warning is logged. Defensive check only. |

The Logs Monitor must never allow a diagnostic failure to interrupt the
original application operation.

Handler failures must not propagate through the logging call and must not
prevent other handlers from receiving records.

---

## 10. Out of scope

The following features are explicitly excluded from the initial
implementation:

- Reading the log file from disk.
- Persisting Monitor contents across process restarts.
- Live Area tables or live Workspace state panels.
- Interactive log-level filtering.
- Search, highlighting or regular-expression filtering.
- Exporting files directly from the dialog.
- Telemetry integration.
- Integration with `ConsoleEditor` or `HistoryEditor`.
- Localization of technical log messages.
- Multiple simultaneous dialog instances.
- Docked presentation.
- Advanced diagnostic analytics.
- Log aggregation across application processes.

These features require separate decisions if they become necessary.

---

## 11. Testing strategy

### 11.1 Routing tests

Test logger-prefix routing and structured tags using table-driven tests.

Cases must include:

- One representative logger per tab.
- Prefix boundary matching.
- Unknown logger fallback.
- `area_snapshot=True`.
- `area_snapshot=False`.
- `area_snapshot=True` on a non-Workspace logger (routed to `General`,
  warning once).
- Logger names that partially resemble valid prefixes but must not match.

No Qt widgets are required.

### 11.2 Formatting tests

Verify:

- Timestamp formatting.
- Level alignment.
- Logger name.
- Message formatting.
- Exception traceback inclusion.
- Stack information inclusion.
- Multiline message preservation.

Tests must use representative `LogRecord` instances.

### 11.3 Buffer tests

Verify:

- Records are stored in the correct tab.
- Maximum capacity is respected.
- Oldest records are discarded first.
- Sequence numbers remain monotonic.
- Snapshot contents and watermark are consistent.
- Concurrent record production does not corrupt the buffer.

### 11.4 Thread-marshalling tests

A record emitted from a worker thread must reach the dialog's slot on the
GUI thread.

Use `QSignalSpy` and a real `QApplication`.

Mark GUI tests with:

```python
@pytest.mark.gui
```

### 11.5 Dialog tests

Verify:

- Dialog instantiation.
- Expected tab order.
- Initial buffer population on first `show()`.
- No duplicate records after initial synchronization.
- Copy Log copies only the active tab.
- Exit hides the dialog.
- Exit does not close the parent.
- New records remain available after the dialog is hidden and reopened.
- Fixed window title `CranioZ — Logs Monitor`.
- Tooltip on the HomePage button resolves through `TranslationService`.

### 11.6 Bootstrap tests

Verify that:

- The handler is installed after `_configure_logging`.
- The handler is passed to `MainWindow`.
- The handler is removed before `task_manager.shutdown()`.
- Handler ownership remains with bootstrap.
- `logs_requested` fired before handler installation is a no-op with a
  warning.

Use an integration test that patches `MainWindow` and inspects root
logger handlers at the relevant lifecycle points.

### 11.7 Workspace contract tests

Verify that `Workspace._apply_default_splitter_sizes` emits:

- One aggregated INFO record per applied layout.
- One DEBUG record per Area.
- `area_snapshot=True` on all snapshot records.
- A shared layout sequence identifier.
- The expected structural fields.

Use `caplog` and assert against the records, not the dialog.

### 11.8 Environment policy tests

Verify that:

- Development configuration permits the diagnostic information required
  for clinical validation.
- Testing configuration follows its configured dataset policy.
- Production configuration sanitizes or excludes clinical identifying
  information.
- All handlers receive records according to the same environment policy.
- Exception tracebacks do not bypass production sanitization.

No test in this suite requires the Logs Monitor to be open.

---

## 12. Implementation decisions

The following decisions are established for the initial implementation:

| Topic | Decision |
|---|---|
| Dialog ownership | One instance owned by `MainWindow` |
| Dialog lifecycle | Hide on close; destroy with parent |
| Window title | Fixed: `CranioZ — Logs Monitor` (not translated) |
| HomePage button tooltip | `Logs` (translated via `TranslationService`) |
| Handler ownership | Bootstrap |
| Handler integration | `QObject` and `logging.Handler` |
| Record representation | Immutable `LogEntry` |
| Routing | Logger prefix plus structured attributes |
| Unknown logger | `General` |
| Inconsistent `area_snapshot` tag | Routed to `General`; warning once per logger |
| Buffer | 5,000 records per tab |
| Overflow | FIFO |
| Initial synchronization | Atomic snapshot with sequence watermark, performed on first `show()` |
| GUI updates | Queued Qt signals |
| Stack traces | Formatted through `logging.Formatter` |
| Areas diagnostics | INFO aggregate and DEBUG per Area |
| Environment policy | Determined by logging configuration, applied centrally before handlers |
| Clinical data in development | Permitted when required for validation |
| Clinical data in production | Sanitized or excluded |
| Persistence | Existing file handler |
| UI filtering | Not implemented |
| Search | Not implemented |
| `Segmentation` routing | Provisional; confirmed in Phase 6A |

Dialog geometry persistence and advanced batching remain optional future
improvements.

---

## 13. References

- `home_page.md` §25 — `logs_requested` signal and Logs button.
- `home_page.md` §26 — HomePage summary and documentation reference.
- `workspace.md` §5.5 — Workspace layout state.
- `workspace.md` §9 — Telemetry and its separation from logging.
- `next_steps.md` §6.2, §7 — Deferred implementation items.
- `main_window.md` §3.1, §9 — Service injection and UI boundaries.
- `adr/ADR-0011` — TaskManager and threading.
- `adr/ADR-0012` — Telemetry architecture.