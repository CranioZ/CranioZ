# Main Window (MainWindow)

## 1. Purpose
*MainWindow* is the top-level application window and hosts the CranioZ Workspace. It presents the main application shell, including the Workspace and UI elements that belong to the window itself.

This document defines the responsibilities and boundaries of the main window. The Workspace document describes Areas, Overlays, layout, and module UI composition. The Clinical Workflows document describes workflow execution. The *steps_panel* document describes the workflow navigation panel hosted as a shared Workspace Overlay.

## 2. Responsibilities
MainWindow is responsible for:

* managing the top-level window lifecycle;
* hosting the Workspace;
* presenting UI elements assigned to the main window, such as the native menu bar and operating-system window controls, when applicable;
* forwarding global user intentions to the appropriate Application-layer capabilities;
* coordinating startup and shutdown requests with the application runtime;
* forwarding project open and close requests to the application runtime without managing the project lifecycle or project data;
* consuming and reflecting application-provided visual and language settings in the surfaces it hosts, such as the theme, icons, and active language;
* presenting relevant application operation state when needed, without performing heavy work inside the window.
* injecting shared application services (`TaskManager`, `TelemetrySink`)   into the `Workspace` and, transitively, into every `EditorContext`.
  MainWindow does not own these services; it forwards the instances it receives from the bootstrap.

MainWindow is a presentation and hosting boundary. It does not implement clinical rules, workflow requirement checks, module operations, or changes to domain or project state. The Project Manager is the application authority for the project lifecycle.

## 3. Relationship to the Workspace
```
QApplication
    └── MainWindow
          ├── Native OS window controls
          ├── Native OS menu bar (optional)
          └── Workspace (content area)
                ├── Top Bar (structural)
                ├── Area Layout Tree
                │   └── Areas (with internal Editor Layout Trees)
                └── Overlays
                    └── steps_panel
```
MainWindow provides the application frame: native window controls and, when applicable, the OS menu bar. Everything else belongs to the Workspace.

The Workspace is responsible for:

* the Top Bar (Painel Superior) — a structural component, not an Overlay;
* the Area Layout Tree and Editor Layout Trees;
* Overlays, including the shared steps_panel.

MainWindow hosts the Workspace and forwards lifecycle events. It does not interpret the Workspace's internal structure.

The Workspace does not know about clinical modules or Flows. MainWindow does not own the clinical workflow either. The Application layer loads the active Flow and module, coordinates transitions, and provides workflow presentation state and the ModuleUISpec to the Workspace.

### 3.1 Service injection

`MainWindow` receives `task_manager: TaskManager` and
`telemetry_sink: TelemetrySink` from the bootstrap and forwards them to
the `Workspace` at construction:

```text
__main__ → MainWindow(task_manager=..., telemetry_sink=...)
                ├── Workspace(task_manager=..., telemetry_sink=...)
                │       ├── EditorContext.task_manager = task_manager
                │       ├── EditorContext.telemetry_sink = telemetry_sink
                │       └── ModuleContext.task_manager (if a module is loaded)
                └── (future) other Workspace hosts
```

## 4. Relationship to modules and clinical workflows
Modules do not own MainWindow and do not replace it when activated. A module provides a ModuleUISpec; the Application layer passes that specification to the Workspace for materialization.

The same main window and Workspace remain in place as the active module changes. In a clinical workflow:

1. The Python workflow engine evaluates the current step and its requirements.
2. The Application layer activates the module associated with the selected step.
3. The Application layer provides the module's ModuleUISpec to the Workspace.
4. The Workspace materializes the composition declared by the module.
5. The shared steps_panel Overlay remains available and receives updated workflow presentation state.

MainWindow may host the Workspace throughout these transitions, but it does not choose the next step or select the module. Those decisions belong to the Application layer and workflow engine.

## 5. Window elements and Workspace content
Main-window UI elements are limited to:

* **Native OS window controls** — title bar, minimize/maximize/close.
* **Native OS menu bar** — when applicable.

There is no status bar in MainWindow. The traditional status bar role is served by a Workspace Area (typically the bottom Area), declared by the module. MainWindow does not host status views.

The Home Page composition and its UI elements, including its own header where applicable, are defined in the Home Page and/or Workspace documentation.

Language, theme, and icon-set preferences are managed by the application's settings service, coordinated by the Application layer. MainWindow does not own or persist these preferences; it and its hosted components consume the active values and update their presentation when the application changes them.

## 6. Asynchronous operations and responsiveness
**MainWindow** does not perform long-running operations or create, manage, or synchronize threads. Image loading, processing, data reads and writes, and other tasks that could block the UI are performed by appropriate services outside the window.

The Application layer coordinates these operations and communicates relevant state to the UI, such as start, progress, completion, cancellation, or error. MainWindow and Workspace components present that state and forward user actions, such as cancellation, without blocking the UI thread.

The implementation of asynchronous work and the choice of concurrency technology belong to the services and execution architecture, not to MainWindow.

## 7. Lifecycle
### 7.1 Startup

```
text
QApplication starts
    ↓
Application runtime initializes (config, logging, event bus, registries)
    ↓
Splash screen shown (optional)
    ↓
MainWindow created (empty shell)
    ↓
Workspace created and installed in MainWindow's content area
    ↓
Project Manager restores the selected context (if applicable)
    ↓
Application activates the appropriate module
    ↓
Workspace materializes the ModuleUISpec
    ↓
Splash screen dismissed; MainWindow shown
```
The splash screen is a temporary top-level window, created by the application runtime before MainWindow is shown. It is not part of the Workspace and not part of MainWindow. It is dismissed when the application is ready.

The Workspace may exist before a project or module is active. The shared steps_panel may exist without an active workflow and receive Flow content when the Application layer loads it.

### 7.2 Close and shutdown
When the user requests that the window close, MainWindow forwards the request to the application runtime and waits for its decision before completing the close.

If a project is active, the runtime coordinates with the Project Manager to close the context and handle pending changes according to application policy. The Project Manager validates and coordinates persistence; MainWindow only presents confirmations or errors requested by the application.

If a long-running operation is in progress, the runtime may offer to cancel the operation, wait, or cancel the close. The policy belongs to the Application layer.

If the user cancels or a required operation fails, the window remains open. The window does not silently discard project, clinical, or workflow state.

Workspace layout state and clinical workflow progress are persisted by their respective owners. Window geometry and other presentation preferences are stored in the application's presentation settings, separately from clinical case state.

## 8. State ownership
State	                                                        Owner
Main-window visibility and geometry	                            MainWindow and presentation settings
Native OS menu bar (when applicable)	                        MainWindow
Active language, theme, icon set	                            Application settings service (Application layer)
Translation resources	                                        Application; UI components present translated text
Top Bar structure	                                            Workspace
Area Layout Tree and Editor Layout Trees	                    Workspace
LayoutState (proportions, visibility, active Editor per Area)	Workspace
OverlayState (Overlay configuration)	                        Workspace
Module UI composition (ModuleUISpec)	                        Module, materialized by the Workspace
Clinical workflow definition and progress	                    Application workflow engine and project/case persistence
Project lifecycle and consistency	                            Project Manager
Read-only project discovery	                                    Project Catalog
Project persistence and physical storage	                    Project Repository and Project Storage
Clinical objects and results	                                Domain and module/application services
Long-running operations state	                                Service responsible, coordinated by the Application layer

| `TaskManager` | Application (constructed by `__main__`, forwarded by `MainWindow`) |
| `TelemetrySink` | Application (constructed by `__main__`, forwarded by `MainWindow`) |
| `Workspace`-scoped Tasks | `Workspace` (cancel on teardown) |
| `Editor`-scoped Tasks | `Editor` (cancel on deactivate / dispose) |

**MainWindow** may host these components, but it is not the source of truth for their state.

## 9. Architectural boundaries
* MainWindow depends on the Workspace as a hosted UI component; the Domain layer does not depend on MainWindow.
* MainWindow does not own the Workspace layout state. The Workspace owns its LayoutState and OverlayState.
* MainWindow does not interpret Top Bar or steps_panel semantics. Those belong to the Workspace.
* MainWindow does not create, update, delete, open, or persist projects directly.
* The Home Page discovers and selects projects; the Workspace works with the open Project Context.
* Clinical modules do not directly manipulate MainWindow internals.
* User actions are forwarded through Application-layer capabilities rather than performing domain operations inside window callbacks.
* Workflow state is supplied by the Application layer; MainWindow does not inspect or calculate clinical requirements.
* MainWindow does not perform heavy work or manage threads.
* Closing the window follows the application's save and shutdown policy.
* Accessibility and internationalization requirements apply to all interfaces presented by the application.

## 10. Testing considerations
Tests for MainWindow should focus on hosting and lifecycle responsibilities:

* the Workspace is installed as the main content component;
* native window controls and menu bar appear in their intended regions;
* startup and close requests are forwarded to the application runtime;
* closing does not proceed when the runtime/Project Manager reports cancellation or failure;
* module and workflow transitions do not recreate the main window;
* global actions invoke Application-layer capabilities rather than changing domain state directly;
* long-running operation state can be presented without blocking the UI;
* the window does not create or manage threads to perform service operations.
* closing `MainWindow` cancels and awaits the `Workspace`'s pending Tasks
  before `closeEvent` returns;
* `TaskManager.shutdown()` is called by the bootstrap after the
  `QApplication` event loop exits, not by `MainWindow`;
* the `TelemetrySink` receives no events from `MainWindow` or its hosted
  components after the window begins closing (any shutdown telemetry is
  emitted before step 1 of §7.3).

Workspace layout, Overlay behavior, workflow transitions, clinical requirement evaluation, and asynchronous task execution are tested at their respective architectural boundaries.
