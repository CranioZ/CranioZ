# Monitor de Logs

**Document type:** Technical specification
**Status:** Planned (not implemented)
**Scope:** Developer/support diagnostic window fed by `logging`
**Last updated:** 2026-11-22

---

## 1. Purpose and scope

The Monitor de Logs is the developer-facing diagnostic window of CranioZ.
It presents `logging` records produced by the application, grouped by
subsystem, in a single non-modal window that can be opened from the
HomePage top bar.

The window exists to answer, during development and support:

- What happened during startup?
- Which component produced this error or warning?
- What is the current layout state of the Workspace Areas?
- Which subsystem is emitting the noise?

The Monitor de Logs is **not**:

- a user-facing console (see §2);
- a clinical history or undo stack (see §2);
- a telemetry channel (see §9 of `workspace.md`);
- a replacement for the log file or stdout (see §6.5).

**Status:** the specification is complete, but no implementation exists.
The `logs_requested` signal is reserved in `home_page.md` §25; the
`Workspace` layout snapshot contract (§7) is not yet emitted. This
document is the single source of truth for the implementation sprint.

---

## 2. Audience and separation of channels

CranioZ exposes three distinct channels to the user. They are not
interchangeable and must not be merged.

| Channel | Audience | Content | Host | Fed by |
|---|---|---|---|---|
| **Console** | Clinical user | Operational messages, warnings, errors and progress produced by the platform and by the running Flow. | `ConsoleEditor` (Bottom Area, declared by a Module). | An application-level notification service (to be defined; **not** `logging`). |
| **History** | Clinical user | Chronological sequence of user operations; enables Undo/Redo. | `HistoryEditor` (Bottom Area, declared by a Module). | The command history maintained by the application. |
| **Monitor de Logs** | Developer / support | `logging` records (DEBUG/INFO/WARNING/ERROR), stack traces, layout snapshots, Task diagnostics, I/O diagnostics. | Floating window, opened from the 📋 button on the HomePage top bar. | A dedicated `logging.Handler` (§6). |

The Console Editor is **not** fed by `logging`. Mixing the two channels
would expose the user to Qt warnings, `mypy` notes, and other
developer-only noise, which is not the Console's purpose. The Console is
a clinical channel; the Monitor de Logs is a developer channel.

This separation is a project invariant. Any future proposal to feed the
Console from `logging`, or to display user-facing messages in the Monitor
de Logs, must be rejected by reference to this section.

---

## 3. Architectural role

The Monitor de Logs belongs to the UI layer. It:

- observes `logging` records;
- renders them grouped by subsystem;
- exposes copy and exit controls.

It does not:

- read the log file from disk (§10);
- know the `Workspace`, the `ProjectIndex`, the `EventBus`, the Scene,
  the Editors, the Modules, or the domain;
- participate in clinical undo/redo;
- modify application state;
- emit telemetry.

It depends on exactly two collaborators:

- a `QtLogHandler` (§6), which it receives or discovers;
- the translation service, for the window title and the button labels.

The Monitor de Logs is a read-only observer. The only state it owns is
the text content of its tabs.

---

## 4. Non-responsibilities

The Monitor de Logs does not:

- configure `logging` (the bootstrap does, see §8);
- install, remove, or filter log handlers;
- parse stack traces or produce diagnostics;
- persist logs across process restarts;
- reorder, deduplicate or aggregate records;
- filter by level from the UI (out of scope, §10);
- replace or duplicate the log file;
- interact with `TelemetrySink`, `EventBus`, `CommandBus`, or any
  Application service.

---

## 5. The `LogsDialog` widget

### 5.1 Window type and identity

- Class: `LogsDialog` in `cranioz/ui/diagnostics/logs_dialog.py`.
- Base class: `QDialog`.
- Window flags: `Qt.WindowType.Tool` (non-modal floating window, stays
  on top of its parent but does not block it).
- Title: **"CranioZ — Monitor de Logs"** (user-facing, pt-BR, per the
  project's user-facing language).
- Icon: the 📋 (`logs`) icon from the `IconProvider`.
- One instance per `MainWindow`. Subsequent clicks of 📋 raise and
  activate the existing instance instead of creating a new one.
- Closing the dialog hides it; it is not destroyed. Its content survives
  until `MainWindow` is destroyed.

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
│   └── Segmentation      (reserved, empty until Phase 4)
└── QHBoxLayout
    ├── QPushButton "Copy Log"
    └── QPushButton "Exit"
```

Each tab contains a `QPlainTextEdit` configured as:

- `setReadOnly(True)`;
- monospace font (the platform default monospace; no custom family);
- `setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)`;
- auto-scroll to the bottom when a new line arrives, unless the user has
  scrolled up (standard "follow tail unless detached" behavior).

The `Segmentation` tab is created but stays empty until Phase 4. It is
not hidden, so that the tab order is stable across versions.

### 5.3 Tab → logger mapping

Routing is decided by `record.name` (the logger name), matched by prefix,
in this order:

| Tab | Logger prefix |
|---|---|
| `Boot` | `cranioz.__main__`, `cranioz.config` |
| `Home Page` | `cranioz.ui.home` |
| `Workspace` | `cranioz.ui.workspace` (except layout snapshots, see §7) |
| `Areas` | `cranioz.ui.workspace` (layout snapshots only, tagged) |
| `Scene` | `cranioz.application.scene`, `cranioz.domain.scene` |
| `Project` | `cranioz.application.project` |
| `Tomography` | `cranioz.editors.builtin.tomography` |
| `Segmentation` | `cranioz.application.segmentation` (reserved) |
| fallback | `Boot` |

The `Areas` tab and the `Workspace` tab share the `cranioz.ui.workspace`
prefix. They are distinguished by a structured tag on the record (see
§7.3), not by the logger name. The `QtLogHandler` reads the tag and routes
accordingly.

The mapping is defined in code as a module-level constant
(`TAB_ROUTES: tuple[tuple[str, str], ...]`), so that adding a new
subsystem is a one-line change and so that the mapping is testable
without instantiating the dialog.

### 5.4 `Copy Log` and `Exit`

- **`Copy Log`** copies the full text of the **currently active tab** to
  the system clipboard, with a trailing newline. It does not copy all
  tabs. It does not include the tab title. Errors are not reported to the
  user; if the clipboard is unavailable, the button is a no-op.
- **`Exit`** closes the dialog. It does **not** close the application and
  does **not** affect the `MainWindow`. The application continues to log;
  the records continue to be buffered per tab so that reopening the
  dialog shows them.

### 5.5 Lifecycle and wiring

The `MainWindow` owns the single `LogsDialog` instance:

```python
# MainWindow.__init__
self._logs_dialog: LogsDialog | None = None

# MainWindow._on_logs_requested
if self._logs_dialog is None:
    self._logs_dialog = LogsDialog(
        log_handler=self._log_handler,  # from bootstrap
        translation_service=self._translation_service,
        icon_provider=self._icon_provider,
        parent=self,
    )
self._logs_dialog.show()
self._logs_dialog.raise_()
self._logs_dialog.activateWindow()
```

The `MainWindow` receives the `QtLogHandler` instance from the bootstrap
(§8), not the other way around. The dialog never installs or removes
handlers.

When `MainWindow` is destroyed, the `LogsDialog` is destroyed with it
(Qt parent ownership). The `QtLogHandler` is removed from the logging
tree by the bootstrap (§8.3), not by the dialog.

---

## 6. The `QtLogHandler`

### 6.1 Responsibility

`QtLogHandler` is a `logging.Handler` subclass that receives every
`LogRecord` produced by the application, routes it to a tab, and appends
it to that tab's buffer. It does not format for the file or for stdout;
those channels continue to be served by the existing handlers (§6.5).

It is the **only** bridge between `logging` and the Monitor de Logs.

### 6.2 Record routing

For each record, the handler:

1. Reads `record.name` and applies the prefix mapping of §5.3.
2. If the resolved tab is `Areas`, applies the tag rule of §7.3.
3. Appends a formatted line to the target tab's buffer.
4. Signals the dialog (if open) to refresh that tab.

Routing is deterministic and stateless. The handler does not reorder
records; records arrive in the order the `logging` framework emits them.

### 6.3 Threading and GUI-thread marshalling

`logging` may be called from any thread (Tasks run off the GUI thread;
see `workspace.md` §3.4). The handler must not touch `QWidget` from a
non-GUI thread.

Implementation:

- The handler is a `QObject`. It defines a signal
  `record_received(str, str, int)` — `(tab, text, level)` — emitted from
  whichever thread produced the record.
- Qt's queued connections marshal the signal to the GUI thread, where the
  dialog's slot appends the line.
- The dialog never reads the handler's internal buffer directly; it
  only receives records via the signal.

This is the same pattern used elsewhere in the project for cross-thread
UI updates. No `QMetaObject.invokeMethod` and no `QTimer.singleShot`
tricks.

### 6.4 Format

Each line is formatted as:

```text
HH:MM:SS LEVEL  name: message
```

- `HH:MM:SS` is the record's `asctime`, truncated to seconds.
- `LEVEL` is the level name, right-aligned to width 8.
- `name` is `record.name`.
- `message` is `record.getMessage()`.

Multiline messages (e.g. exception tracebacks) are appended verbatim
after the first line, with no additional prefix. The tab preserves the
original line structure.

The format is defined once, in a module-level constant
(`LINE_FORMAT: str`), so that tests can assert against it without
duplicating the string.

### 6.5 Interaction with existing handlers

The `QtLogHandler` is **additive**. It does not replace the file handler,
the stdout handler, or the existing `LoggingTelemetrySink`. All three
continue to receive records.

Consequence: log volume is not increased, but it is duplicated across
channels. This is intentional — the Monitor de Logs is a view, not a
logger.

The handler sets `self.setLevel(logging.DEBUG)` so that DEBUG records
reach the dialog. The application's global level (set by
`_configure_logging`) continues to apply to the root logger; the handler
does not raise it.

---

## 7. The `Areas` tab — contract with the Workspace

### 7.1 What is logged

The `Workspace` emits two kinds of layout records:

- an **aggregated** record per applied layout (§7.2, INFO);
- a **per-Area** record per Area in the layout (§7.2, DEBUG).

Records describe only Area-level state: `area_id`, `placement`,
`visible`, `size`, number of `editors`, layout shape. They do **not**
describe Editors, Tools, Toolbars, Modules, or clinical data.

### 7.2 Levels

| Level | Frequency | Content |
|---|---|---|
| `INFO` | Once per `_apply_default_splitter_sizes` completion (which is already debounced by 50 ms; see `workspace.py` module docstring). | Aggregated: visible placements, per-Area sizes, root size, region bounds. |
| `DEBUG` | Once per Area per applied layout. | Per-Area: `area_id`, `placement`, `visible`, `size`, `editors`, `layout`. |

The existing `_logger.info("DEBUG: Vertical splitter ...")` call in
`Workspace._compute_vertical_sizes` must be lowered to `debug` when this
contract is implemented, so that the `Areas` tab shows one INFO line per
applied layout rather than one INFO line per splitter.

### 7.3 Format and routing tag

Aggregated line (INFO):

```text
layout applied areas=3 visible=[central] sizes=[0,960,0]
    root=1200x800 regions={central:1200x800,left:placeholder,
    right:placeholder,bottom:placeholder}
```

Per-Area lines (DEBUG), one per Area:

```text
area.central placement=central visible=True size=1200x800
    editors=2 layout=SPLIT(H)
area.left    placement=left    visible=False size=0x0
    editors=1 layout=LEAF
```

The routing tag is carried on the record as `record.area_snapshot =
True`. The `QtLogHandler` routes records with this tag to the `Areas`
tab even though their logger name is `cranioz.ui.workspace`. Records
from the same logger without the tag go to the `Workspace` tab.

The `extra={"area_snapshot": True}` parameter is the only structured
extension of the `logging` call. It is not a substitute for the
formatted string; the string is what the user reads, and the tag is what
the handler uses.

### 7.4 Emission point

The aggregated INFO record is emitted at the end of
`Workspace._apply_default_splitter_sizes`, after sizes are applied and
before the `QTimer.singleShot(0, self._reposition_overlays)` call. This
guarantees that the sizes reported are the ones applied.

The per-Area DEBUG records are emitted in the same block, one per
`self._build_result.areas`.

The `Workspace` does not emit snapshot records anywhere else. Layout
changes that do not go through `_apply_default_splitter_sizes` are not
logged as snapshots; they appear as ordinary `cranioz.ui.workspace`
records in the `Workspace` tab, if any.

### 7.5 What must not be logged

- Editor identifiers, Editor state, Tool or Toolbar names.
- Scene identifiers, clinical object identifiers.
- Project identifiers, project names, patient names, file paths.
- Telemetry-shaped records (those go through `TelemetrySink`; see
  `workspace.md` §9).
- Anything that would be PII or PHI.

The `Areas` tab is a structural view of the Workspace, not a clinical
view.

---

## 8. Bootstrap wiring

### 8.1 Where the handler is installed

The `QtLogHandler` is created in `cranioz.__main__`, inside `main()`,
**after** `_configure_logging(config)` and **before** the `MainWindow` is
constructed. It is added to the root logger with
`logging.getLogger().addHandler(handler)`.

The handler instance is then passed to `MainWindow` as a keyword
argument, alongside `task_manager` and `telemetry`.

### 8.2 Ordering relative to `_configure_logging`

`_configure_logging` runs first so that the file and stdout handlers are
installed before the `QtLogHandler`. The order matters only for
readability; the root logger dispatches to all handlers in registration
order, and the `QtLogHandler` does not depend on the others.

Records emitted **before** `_configure_logging` runs (e.g. during
`ConfigurationLoader().load()`) are not captured by any handler and are
not shown in the dialog. This is acceptable: the dialog is opened by the
user after startup, and early startup messages are in the log file if
the file handler is configured early enough (which is a separate
concern).

### 8.3 Shutdown

The handler is removed from the root logger by the bootstrap, in the
shutdown path after the `QApplication` event loop exits, before
`task_manager.shutdown()`. The order is:

```python
exit_code = app.exec()
logging.getLogger().removeHandler(handler)
task_manager.shutdown()
```

This prevents records emitted during `task_manager.shutdown()` from
reaching a `QObject` whose event loop has already exited. The dialog is
destroyed with the `MainWindow`, which is destroyed before the handler
is removed.

The handler is **not** closed by the dialog. Ownership is the
bootstrap's, not the dialog's.

---

## 9. Error handling and failure modes

| Failure | Behavior |
|---|---|
| The `QtLogHandler` cannot marshal a record to the GUI thread (e.g. the dialog was destroyed). | The handler silently drops the record. The file and stdout handlers continue to receive it. No exception escapes. |
| The dialog is closed while records are arriving. | Records continue to be buffered per tab in the handler's internal store; they are appended to the dialog's `QPlainTextEdit` when it is reopened. |
| The clipboard is unavailable during `Copy Log`. | The button is a no-op. No error is shown. |
| A record has no recognizable `record.name`. | Routed to `Boot`. |
| A record carries `area_snapshot=True` but the dialog is not open. | Buffered for the `Areas` tab, same as any other record. |
| `logging` is configured with `disable_existing_loggers=True` after the handler is installed. | The handler may stop receiving records. This is a configuration error, not a handler error; it is out of scope for the dialog. |

The Monitor de Logs does not implement recovery logic. Its failure modes
are silent by design.

---

## 10. Out of scope

The following are explicitly not part of the Monitor de Logs and must
not be added without a separate decision:

- reading the log file from disk (the dialog shows in-memory records
  since process start; `Copy Log` is the export path);
- live Area tables or live state panels (the `Areas` tab is textual);
- log level filtering from the UI;
- search, highlight, or regex filtering;
- saving the dialog's content to a file from within the dialog;
- telemetry integration;
- merging with the Console Editor or the History Editor;
- localization of log content (records are not translated; only the
  window title, the tab labels, and the two buttons are translated);
- multiple simultaneous instances of the dialog;
- docked (non-floating) presentation.

---

## 11. Testing strategy

- **Routing tests.** `QtLogHandler` routes records by `record.name`
  prefix and by `area_snapshot` tag. Table-driven: one case per tab,
  plus the fallback and the tag case. No Qt widget is instantiated.
- **Format tests.** `LINE_FORMAT` produces the expected string for a
  representative record. Multiline messages are preserved.
- **Thread-marshalling test.** A record emitted from a worker thread
  reaches the dialog's slot on the GUI thread. Uses `QSignalSpy` and a
  real `QApplication`; marked `@pytest.mark.gui`.
- **Dialog tests.** `LogsDialog` instantiates; tabs exist in the expected
  order; `Copy Log` copies only the active tab; `Exit` hides the dialog
  and does not close the parent.
- **Bootstrap test.** `main()` installs the handler after
  `_configure_logging` and removes it before `task_manager.shutdown()`.
  Verified by an integration test that patches `MainWindow` and inspects
  the root logger's handlers at the right points.
- **Workspace contract tests.** `Workspace._apply_default_splitter_sizes`
  emits one INFO record with `area_snapshot=True` and one DEBUG record
  per Area, with the fields of §7.2. Uses `caplog` and asserts on the
  records, not on the dialog.

No test in this suite requires the Monitor de Logs to be open.

---

## 12. Open questions (deferred to implementation)

- Should the `Areas` tab preserve history across layout changes, or
  reset on each `load_spec`? Current spec: preserve (it is a log, not a
  state view). Revisit if the volume is problematic.
- Should the dialog remember its geometry across application restarts?
  Current spec: no. If needed, it belongs to the presentation settings,
  not to the dialog.
- Should `Copy Log` offer "all tabs" as a secondary action? Current
  spec: no. `Copy Log` copies the active tab only.
- Should the handler buffer be bounded (e.g. last N records per tab) to
  avoid unbounded memory growth? Current spec: unbounded, matching the
  log file. Revisit if the application is expected to run for days.

---

## 13. References

- `home_page.md` §25 — `logs_requested` signal, 📋 button (reserved).
- `home_page.md` §26 — summary and pointer to this document.
- `workspace.md` §5.5, §9 — layout state, telemetry (distinct channel).
- `next_steps.md` §6.2, §7 — deferred item and future sprint.
- `main_window.md` §3.1, §9 — service injection, UI boundaries.
- `adr/ADR-0011` — TaskManager and threading.
- `adr/ADR-0012` — telemetry (not the channel used here).