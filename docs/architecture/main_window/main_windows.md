# Main Window (`MainWindow`)

## 1. Purpose

`MainWindow` is the top-level application window and hosts the CranioZ Workspace. It presents the main application shell, including the Workspace and UI elements that belong to the window itself.

This document defines the responsibilities and boundaries of the main window. The Workspace document describes Areas, Overlays, layout, and module UI composition. The Clinical Workflows document describes workflow execution. The `steps_panel` document describes the workflow navigation panel hosted as a shared Workspace Overlay.

This document is a proposed architecture for technical validation. Product decisions that have not yet been confirmed are identified as such.

## 2. Responsibilities

`MainWindow` is responsible for:

- managing the top-level window lifecycle;
- hosting the Workspace;
- presenting UI elements assigned to the main window, such as the native menu bar and operating-system window controls, when applicable;
- forwarding global user intentions to the appropriate Application-layer capabilities;
- coordinating startup and shutdown requests with the application runtime;
- forwarding project open and close requests to the application runtime without managing the project lifecycle or project data;
- consuming and reflecting application-provided visual and language settings in the surfaces it hosts, such as the theme, icons, and active language;
- presenting relevant application operation state when needed, without performing heavy work inside the window.

`MainWindow` is a presentation and hosting boundary. It does not implement clinical rules, workflow requirement checks, module operations, or changes to domain or project state. The `Project Manager` is the application authority for the project lifecycle and coordinates its operations with the catalog, access policies, repository, and storage.

## 3. Relationship to the Workspace

```text
QApplication
    └── MainWindow
          ├── Main-window UI elements
          └── Workspace
                ├── Areas and their Editors
                └── Overlays, including the shared steps_panel
```

The proposed arrangement is for the application runtime to create and maintain a Workspace instance, which `MainWindow` receives and installs in its content area. The window may forward lifecycle events, while the Workspace manages its own Areas, layout tree, and Overlay positioning.

The Workspace hosts Areas and Overlays and does not know about clinical modules or Flows. `MainWindow` does not own the clinical workflow either. The Application layer loads the active Flow and module, coordinates transitions, and provides workflow presentation state and the `ModuleUISpec` to the UI components that need them.

## 4. Relationship to modules and clinical workflows

Modules do not own `MainWindow` and do not replace it when activated. A module provides a `ModuleUISpec`; the Application layer passes that specification to the Workspace for materialization.

The same main window and Workspace remain in place as the active module changes. In a clinical workflow:

1. The Python workflow engine evaluates the current step and its requirements.
2. The Application layer activates the module associated with the selected step.
3. The Application layer provides the module's `ModuleUISpec` to the Workspace.
4. The Workspace materializes the composition declared by the module.
5. The shared `steps_panel` Overlay remains available and receives updated workflow presentation state.

`MainWindow` may host the Workspace throughout these transitions, but it does not choose the next step or select the module. Those decisions belong to the Application layer and workflow engine.

## 5. Window elements and Workspace content

Main-window UI elements are those outside the Workspace composition, such as native window controls and, when applicable, the native menu bar. The Workspace remains responsible for its Areas and Overlays, including the shared `steps_panel`.

A console or status view, for example, is hosted in a Workspace Area when declared by a module; it does not become a `MainWindow` status bar without an explicit application-level requirement. The Home Page composition and its UI elements, including the Top Bar where applicable, should be defined in the Home Page and/or Workspace documentation, according to the responsibility established in those documents.

Language, theme, and icon-set preferences are managed by the application's settings service, coordinated by the Application layer. `MainWindow` does not own or persist these preferences; it and its hosted components consume the active values and update their presentation when the application changes them. The application provides translation resources, while each component presents its text in the active language.

## 6. Asynchronous operations and responsiveness

`MainWindow` does not perform long-running operations or create, manage, or synchronize threads. Image loading, processing, data reads and writes, and other tasks that could block the UI are performed by appropriate services outside the window.

The Application layer coordinates these operations and communicates relevant state to the UI, such as start, progress, completion, cancellation, or error. `MainWindow` and Workspace components present that state and forward user actions, such as cancellation, without blocking the UI thread. The implementation of asynchronous work and the choice of concurrency technology belong to the services and execution architecture, not to `MainWindow`.

## 7. Lifecycle

### 7.1 Startup

```text
QApplication starts
    ↓
Application runtime and registries initialize
    ↓
Workspace and shared UI components are created
    ↓
MainWindow is created and receives the Workspace
    ↓
An optional splash screen presents startup status
    ↓
The application restores the selected context through the Project Manager, if applicable
    ↓
The application activates the appropriate module
    ↓
The Workspace materializes the module's ModuleUISpec
    ↓
MainWindow is shown and the splash screen is dismissed
```

If adopted, the splash screen is a temporary startup interface coordinated by the application runtime. It is neither `MainWindow` nor part of the Workspace. Its display and dismissal should track actual startup progress; failures should be reported through the appropriate UI. Whether the main window appears before or after restoration is complete remains a product and implementation decision.

The Workspace may exist before a project or module is active. The shared `steps_panel` may exist without an active workflow and receive Flow content when the Application layer loads it. When a project is restored, the application asks the `Project Manager` to open it and build the `Project Context`; the window only hosts the resulting UI.

### 7.2 Close and shutdown

When the user requests that the window close, `MainWindow` forwards the request to the application runtime and waits for its decision before completing the close. If a project is active, the runtime coordinates with the `Project Manager` to close the context and handle pending changes according to application policy. The `Project Manager` validates and coordinates persistence; `MainWindow` only presents confirmations or errors requested by the application. If the user cancels or a required operation fails, the window remains open. The window does not silently discard project, clinical, or workflow state.

The close contract must allow saves or in-progress operations to finish, be cancelled, or be refused according to application policy. The runtime authorizes closing only after the `Project Manager` and other involved services have completed or declined their shutdown responsibilities. The window closes only after receiving this explicit authorization.

Workspace layout state and clinical workflow progress are persisted by their respective owners. Window geometry and other presentation preferences are stored in the application's presentation settings, separately from clinical case state. The specific storage format and mechanism are left to the implementation.

## 8. State ownership

| State | Owner |
| --- | --- |
| Main-window visibility and geometry | `MainWindow` and application presentation settings |
| Active language, theme, and icon set | Application settings service, coordinated by the Application layer |
| Translation resources | Application; UI components present translated text |
| Workspace Area tree, splits, and Overlay placement | Workspace |
| Module UI composition | Module `ModuleUISpec`, materialized by the Workspace |
| Clinical workflow definition and progress | Application workflow engine and project/case persistence |
| Project lifecycle and consistency | `Project Manager` |
| Read-only project discovery | `Project Catalog` |
| Project persistence and physical storage | Project Repository and Project Storage, coordinated by the `Project Manager` |
| Clinical objects and results | Domain and module/application services |
| State of long-running and asynchronous operations | The service responsible for the operation, coordinated by the Application layer |

`MainWindow` may host these components, but it is not the source of truth for their state.

## 9. Architectural boundaries

- `MainWindow` depends on the Workspace as a hosted UI component; the Domain layer does not depend on `MainWindow`.
- `MainWindow` does not create, update, delete, open, or persist projects directly; lifecycle requests are forwarded to the runtime/Application layer and executed by the `Project Manager`.
- The Home Page discovers and selects projects; the Workspace works with the open `Project Context`. Neither replaces the `Project Manager` or accesses persistence directly.
- Clinical modules do not directly manipulate `MainWindow` internals.
- User actions are forwarded through Application-layer capabilities rather than performing domain operations inside window callbacks.
- Workflow state is supplied by the Application layer; `MainWindow` does not inspect or calculate clinical requirements.
- `MainWindow` does not perform heavy work or manage threads; specialized services perform asynchronous operations, and the Application layer coordinates their interaction with the UI.
- Workspace layout state and clinical workflow progress are persisted separately; project state follows the persistence boundary coordinated by the `Project Manager`.
- Closing the window follows the application's save and shutdown policy.
- Accessibility and internationalization requirements apply to the interfaces presented by the application, including `MainWindow`, the Workspace, and modules. Shared criteria should be defined in the presentation architecture and the product's cross-cutting requirements.

## 10. Testing considerations

Tests for `MainWindow` should focus on hosting and lifecycle responsibilities:

- the Workspace is installed as the main content component;
- window-level UI elements appear in their intended regions;
- startup and close requests are forwarded to the application runtime;
- closing does not proceed when the runtime/`Project Manager` reports cancellation or failure to close the active context;
- module and workflow transitions do not recreate the main window;
- global actions invoke Application-layer capabilities rather than changing domain state directly;
- long-running operation state can be presented without blocking the UI;
- the window does not create or manage threads to perform service operations.

Workspace layout, Overlay behavior, workflow transitions, clinical requirement evaluation, and asynchronous task execution should be tested at their respective architectural boundaries.

## 11. Decisions pending validation

- Confirm whether a splash screen will be shown and during which startup stages.
- Confirm when `MainWindow` should be shown relative to project/case restoration and module activation.
- Define the coordination contract among the runtime, `Project Manager`, and UI for opening/closing projects, including cancellation and persistence failures.
- Define the technical asynchronous contract among the runtime, Application layer, services, and UI, including cancellation and shutdown with operations in progress.
- Define shared accessibility and internationalization requirements for the UI.
- Confirm which documents own the Home Page composition and Top Bar, and keep cross-references only to documents that exist.
