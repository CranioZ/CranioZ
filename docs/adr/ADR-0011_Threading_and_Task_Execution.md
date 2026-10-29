# ADR-0011: Threading and Task Execution

**Status:** Accepted
**Date:** 2026-10-22
**Deciders:** Architecture team
**Related:** modules.md §7.1, §7.2; editor.md §15; scene.md §41; implementation.md §6.4; ADR-0007

---

## 1. Context

CranioZ is a PySide6/VTK application that must remain responsive during
long-running clinical operations: DICOM import, segmentation,
registration, mesh processing, and AI-assisted planning. These
operations can take seconds to minutes and must not block the GUI event
loop.

Three incompatible threading models coexisted in the early drafts:

- **Model A — implicit threads.** Components create `QThread`,
  `ThreadPoolExecutor`, or `asyncio` loops as needed. Simple to write,
  impossible to reason about: every component owns its threading
  policy, cancellation is ad-hoc, and the GUI thread is corrupted by
  any component that touches a `QWidget` from a worker.
- **Model B — single thread.** Everything runs on the GUI thread;
  long operations are broken into `QTimer` chunks. Keeps the event
  loop responsive only in theory; a single long-running VTK call
  freezes the UI.
- **Model C — explicit task abstraction.** A single `TaskManager`
  owns every off-thread operation. The GUI thread runs UI and
  lifecycle code; workers run `Task` instances. Cancellation,
  progress, and error propagation are first-class.

This ADR adopts **Model C** and defines the `TaskManager` contract.
The modules.md, editor.md, and scene.md documents reference this ADR
instead of defining threading rules themselves.

## 2. Decision

### 2.1 Threading model

The application has exactly two kinds of threads: the **GUI thread**
(the thread that owns the `QApplication`) and **worker threads** owned
by the `TaskManager`. No other thread exists.

| Operation | Thread |
|---|---|
| `QApplication` event loop | GUI |
| Creation, modification, or destruction of any `QWidget` | GUI |
| Creation, modification, or destruction of any VTK render window, interactor, actor, or mapper | GUI |
| Reading `Scene`, `ProjectContext`, or any domain object | GUI |
| Executing a Command through the `CommandBus` | GUI (synchronous) |
| Module lifecycle hooks (`on_load`, `on_activate`, `on_deactivate`, `on_unload`) | GUI |
| Editor lifecycle hooks (`initialize`, `activate`, `deactivate`, `dispose`) | GUI |
| Workspace operations (`load_spec`, `clear`, overlay reposition) | GUI |
| Long-running computation (DICOM parse, segmentation, registration, mesh processing, AI inference) | Worker |
| File I/O larger than a few milliseconds | Worker |
| Background maintenance (cache warming, telemetry flush) | Worker |

The rule is not "every heavy operation is a Task". It is "every
operation that *can* take more than a few milliseconds is a Task".
The `TaskManager` is the only mechanism for off-thread work.

### 2.2 TaskManager contract

```python
class TaskManager(Protocol):
    def dispatch(
        self,
        task: Task,
        *,
        on_progress: Callable[[float], None] | None = None,
        on_result: Callable[[Any], None] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> TaskHandle: ...


class TaskHandle(Protocol):
    @property
    def id(self) -> str: ...
    @property
    def state(self) -> TaskState: ...
    def cancel(self) -> None: ...
    def wait(self, timeout: float | None = None) -> None: ...


class Task(Protocol):
    def run(
        self,
        progress: Callable[[float], None],
        cancel_token: CancelToken,
    ) -> Any: ...


class CancelToken(Protocol):
    @property
    def is_cancelled(self) -> bool: ...
    def raise_if_cancelled(self) -> None: ...


class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
```

dispatch returns immediately. The callbacks (on_progress,
on_result, on_error, on_cancel) are invoked on the GUI
thread, even though the Task runs on a worker. This is the only
correct way for a Task to touch QWidget or VTK: it must marshal the
result back to the GUI thread, and the TaskManager does that
marshalling.

dispatch on a task that is already dispatched raises
TaskAlreadyDispatched. TaskHandle.cancel on a completed, failed,
or cancelled task is a no-op. TaskHandle.wait blocks the calling
thread until the task reaches a terminal state or the timeout expires.

2.3 Prohibited patterns
The following are contract violations, not style preferences:

Creating a QThread, ThreadPoolExecutor, ProcessPoolExecutor,
asyncio event loop, or raw threading.Thread outside the
TaskManager implementation.

Touching a QWidget, VTK render object, or any GUI-thread state
from a Task.run.

Calling QApplication.processEvents() from anywhere. It is a
symptom of blocking the GUI thread, not a fix.

Calling time.sleep in a lifecycle hook or in Task.run without
checking the CancelToken at least once per second.

Mutating the Scene, Project, or any domain object from
Task.run. Tasks may read immutable snapshots; mutations are
Commands, which run on the GUI thread.

2.4 Cancellation and lifecycle
Cancellation is cooperative. TaskHandle.cancel() sets the
CancelToken; the Task decides when to stop, typically between
steps of a loop. A Task that ignores the token will run to
completion; the TaskManager does not interrupt it. The
TaskManager guarantees that a cancelled task's on_progress and
on_result are not called after cancellation is observed, and that
on_cancel is called exactly once.

The lifecycle rules:

When the Module is unloaded, the ModuleLoader cancels tasks
dispatched through that Module's ModuleContext.task_manager
binding. Tasks are scoped to the Module, not to the application.

When the Editor is deactivated or disposed, the EditorContext
cancels tasks dispatched through its task_manager binding.

When the Workspace is destroyed, the Workspace cancels all
remaining tasks associated with it, then waits for them to reach a
terminal state or the configured shutdown timeout.

When the application exits, TaskManager.shutdown() cancels
all tasks and waits for a configurable grace period (default 5s)
before terminating workers.

Cancellation does not roll back partial effects. A Task that
must produce persistent output writes it through Commands after the
task completes; a Command in a cancelled transaction is rolled back
by the CommandBus (ADR-0007 §2.3), not by the TaskManager.

2.5 Progress and result delivery
progress(value) is called from Task.run. The TaskManager
queues it to the GUI thread before invoking the caller's
on_progress. value is [0.0, 1.0], or negative for
"indeterminate". Non-monotonic progress is the caller's
responsibility; the TaskManager does not reorder or clamp.

on_result(value) is called once, on the GUI thread, after
Task.run returns. If Task.run raises, on_result is not
called and on_error is.

If on_progress, on_result, or on_error raises, the
TaskManager logs the error and does not affect the task's
state. A raising callback is a UI bug, not a task failure.

on_cancel is called once on the GUI thread when the task
observes cancellation and exits. TaskState.CANCELLED is distinct
from TaskState.FAILED.

2.6 Error propagation
Task.run exceptions are caught by the TaskManager and delivered
to on_error. The traceback is preserved in the task's diagnostic
record. If on_error is not provided, the TaskManager logs the
error at ERROR level and marks the task FAILED.

CancelledError (raised by CancelToken.raise_if_cancelled) is
handled specially: it transitions the task to CANCELLED, not
FAILED, and calls on_cancel. A task that raises any other
exception after cancellation is still FAILED; the cancellation
token is advisory.

2.7 Implementation
The TaskManager Protocol lives in
cranioz/application/tasks/task_manager.py. The default
implementation, QtTaskManager, lives in
cranioz/infrastructure/tasks/qt_task_manager.py. It uses
QThreadPool for CPU-bound tasks and ProcessPoolExecutor for
tasks that declare process_safe = True (used only when the task
spends most of its time in Python code that holds the GIL; VTK and
ITK release the GIL, so most tasks stay on QThreadPool).

The TaskManager is a single instance per application,
constructed by __main__ and injected into the MainWindow, which
injects it into the Workspace, which exposes it via
Workspace.task_manager(). It is also injected into each
ModuleContext and EditorContext.

3. Rationale
3.1 Model C is the only model compatible with ADR-0002 and ADR-0007
ADR-0002 establishes that EditorContext is per-Editor and shared
services are references. ADR-0007 establishes that every persistent
mutation goes through a Command, and Commands are synchronous. A
component that spawns its own thread and touches a QWidget from it
violates ADR-0002 (widgets belong to the GUI thread) and ADR-0007
(mutations are Commands, which run on the GUI thread). The
TaskManager is the single boundary between the two worlds.

3.2 Cooperative cancellation is the only safe model for VTK and ITK
VTK and ITK calls are not interruptible from outside. The only
correct cancellation is at task boundaries: the task checks the
token between VTK calls and returns early. A preemptive model would
require cancelling the VTK call, which the library does not support.

3.3 Progress and results cross the thread boundary exactly once
A Task.run that updates QProgressBar directly corrupts Qt state.
A Task.run that calls on_result from the worker thread has the
same problem. Marshalling all callbacks to the GUI thread centralizes
the boundary: the Task sees only progress and cancel_token,
both of which are safe to call from a worker.

3.4 Task scoping matches ownership
Tasks are cancelled when their owner (Module, Editor, Workspace) goes
away. This is consistent with ADR-0007's transaction boundaries and
with modules.md's activation-scope model: a resource that outlives
its owner is a bug, not a feature.

3.5 The 5-second shutdown grace period is a clinical requirement
TaskManager.shutdown() waits up to 5 seconds for tasks to observe
cancellation. Clinical operations (DICOM import, mesh processing)
may have written partial files; the TaskManager lets them finish
cleanup before terminating. A task that exceeds 5 seconds is
terminated by the OS; its diagnostic record notes the truncation.

4. Consequences
4.1 Positive
One threading policy for the entire application.

GUI thread integrity is a contract, not a convention.

Cancellation, progress, and error propagation are uniform.

Task scoping matches component lifecycle.

The TaskManager boundary is testable with fake tasks.

4.2 Negative
Every long operation requires a Task wrapper, even trivial ones.
The TaskManager is not a general-purpose Executor; it expects
the Task Protocol.

Progress reporting requires the Task to accept a progress
callback. Tasks that cannot report progress pass a no-op.

The 5-second shutdown grace period means the application does not
exit instantly when a task is running. This is deliberate.

4.3 Neutral
asyncio is not used. The TaskManager is a Qt-native abstraction
because CranioZ is a Qt application.

ProcessPoolExecutor is available but rare. VTK/ITK release the
GIL, so most tasks stay on QThreadPool.

5. Rules applied by this ADR
Every QWidget, VTK render object, and domain object is touched
only from the GUI thread.

Every long-running operation is a Task dispatched through the
TaskManager.

The TaskManager is the only mechanism for off-thread work.

Task.run receives a progress callback and a CancelToken; it
must call progress at least once per second and must check the
token at least once per second.

Task.run callbacks (on_progress, on_result, on_error,
on_cancel) are invoked on the GUI thread.

Cancellation is cooperative. The TaskManager does not interrupt
a running Task.

Tasks are scoped to their owner (Module, Editor, or Workspace)
and are cancelled when the owner goes away.

TaskManager.shutdown() cancels all tasks and waits up to 5
seconds before terminating workers.

Components do not create QThread, ThreadPoolExecutor,
ProcessPoolExecutor, asyncio loops, or raw threads.

QApplication.processEvents() is prohibited.

time.sleep in a lifecycle hook is prohibited; a Task may
sleep only while checking the CancelToken.

The TaskManager is a single application-wide instance,
injected via MainWindow, Workspace, ModuleContext, and
EditorContext.

6. Rejected alternatives
6.1 Implicit threads in each component
Rejected. Every component would need its own threading policy,
cancellation, and error handling. The GUI thread would be corrupted
by any component that violates the rule.

6.2 QTimer-based chunking on the GUI thread
Rejected. It keeps the event loop responsive only in theory. A single
VTK call that takes 500 ms freezes the UI; no chunking can fix that.
The TaskManager is the only correct model.

6.3 asyncio as the task model
Rejected. CranioZ is a Qt application; asyncio would require an
event loop adapter (qasync or asyncio-qt) and would not integrate
with QThreadPool, VTK, or the CommandBus. The TaskManager is
Qt-native by design.

6.4 dispatch_and_wait in the public API
Rejected. A synchronous dispatch from the GUI thread blocks the event
loop, which is exactly what the TaskManager exists to prevent.
Synchronous operations that take a few milliseconds run directly on
the GUI thread; operations that take longer use dispatch with
on_result. There is no dispatch_and_wait.

6.5 Preemptive cancellation
Rejected. VTK and ITK do not support interrupting a running call.
Cooperative cancellation at task boundaries is the only correct
model.

6.6 No task scoping (application-global tasks)
Rejected. A task that outlives its owner can write to a torn-down
Scene or a destroyed QWidget. Scoping tasks to the Module,
Editor, or Workspace that dispatched them makes lifecycle bugs
visible.

7. Summary
The TaskManager is the single boundary between the GUI thread and
worker threads in CranioZ. It owns dispatch, cancellation, progress,
and error propagation for every long-running operation. The GUI
thread runs UI and domain code; workers run Task.run. Cancellation
is cooperative; callbacks are marshalled to the GUI thread; tasks
are scoped to their owner. Components do not create threads, event
loops, or processEvents() calls; the TaskManager is the only
mechanism.
