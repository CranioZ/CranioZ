# Application Startup

## 1. Purpose

Define how CranioZ initializes, presents its HomePage, prepares secondary resources, activates projects and workflows, and shuts down.

The startup architecture must provide:

- Predictable and responsive application startup.
- A functional HomePage before secondary initialization begins.
- Strict separation between application initialization and clinical resource activation.
- Lazy loading of feature-specific dependencies.
- Controlled background operations.
- Reliable activation, rollback, and shutdown.
- Measurable performance and straightforward debugging.

The primary objective is to minimize unnecessary initialization while keeping the architecture simple, deterministic, and maintainable.

## 2. Architectural Principles

### 2.1 Initialization Boundaries

Startup is divided into four stages:

1. **Application Boot** — initializes essential application infrastructure.
2. **HomePage Initialization** — constructs and presents the functional HomePage.
3. **Background Initialization** — prepares secondary, non-clinical application resources.
4. **Project/Workflow Activation** — initializes resources explicitly required by the selected project and workflow.

Each stage has a defined responsibility. Resources must not be initialized earlier than necessary.

### 2.2 Core Principles

- **UI-first:** the HomePage must become usable before non-essential initialization begins.
- **Lazy loading:** feature-specific implementations are loaded only when required.
- **On-demand activation:** clinical resources are initialized only after an explicit project or workflow activation request.
- **Non-blocking execution:** secondary operations must not block the main thread.
- **Dependency-aware execution:** initialization follows declared dependencies.
- **Failure isolation:** optional initialization failures must not compromise the application.
- **Deterministic behavior:** initialization must not depend on historical usage or predictive mechanisms.
- **Resource efficiency:** unnecessary imports, allocations, and background operations must be avoided.

## 3. Initialization Stages

### 3.1 Application Boot

Application Boot initializes only the infrastructure required to construct the application shell and its initial screen.

Typical responsibilities:

- Load essential application configuration.
- Initialize basic logging.
- Create or retrieve `QApplication`.
- Initialize essential application paths.
- Create shared infrastructure services required by the HomePage.
- Initialize minimum event and task infrastructure.
- Register lightweight application-level metadata.
- Construct the dependencies required by `MainWindow`.

Boot must not initialize:

- Clinical modules.
- Project-specific resources.
- Patient data.
- Workspace instances.
- Editor implementations.
- Clinical tools or workflows.
- VTK, ITK, PyDICOM, OCCT, or other feature-specific scientific dependencies.

Application Boot should remain independent of the clinical feature set.

### 3.2 HomePage Initialization

HomePage Initialization constructs and presents the complete initial application interface.

Responsibilities include:

- Construct `MainWindow`.
- Initialize the HomePage and its navigation.
- Display recent projects and available workflows.
- Retrieve lightweight project and workflow metadata.
- Load essential appearance and localization settings.
- Connect UI actions to application services.
- Present loading, empty, and error states when necessary.

The HomePage must be functional before secondary background initialization begins.

It must not require:

- Project data loading.
- Patient data loading.
- Workspace construction.
- Clinical module activation.
- Editor implementation loading.
- Scientific libraries required exclusively by clinical workflows.

#### 3.2.1 Project Catalog

Project discovery must not require recursively scanning the entire project directory during every application startup.

`ProjectCatalog` should retrieve lightweight metadata through `FilesystemProjectRepository`, preferably using a persistent index.

The index may use SQLite or another suitable persistence mechanism and should contain only information required for project discovery, such as:

- Project ID.
- Display name.
- Project location.
- Creation and modification timestamps.
- Project classification.
- Availability or indexing status.

The index must not contain patient data or replace the project's authoritative data files.

Expected behavior:

- Retrieve indexed metadata efficiently.
- Avoid opening project files merely to display project entries.
- Update metadata incrementally when changes are detected.
- Perform broader discovery and index reconciliation in a controlled background operation.
- Recover from missing, outdated, or corrupted indexes without making normal startup dependent on a complete filesystem scan.

`ProjectCatalog` should expose a stable application-level interface independently of the underlying indexing implementation.

### 3.3 Background Initialization

Background Initialization begins only after the HomePage has been presented and is responsive.

Its purpose is to prepare secondary application resources that are useful but not required for the initial presentation.

Possible operations include:

- Refresh project catalog metadata.
- Reconcile the persistent project index.
- Load additional localization catalogs.
- Prepare extended appearance resources.
- Build optional application-level caches.
- Retrieve non-essential application metadata.
- Perform optional update checks.

Background Initialization must not load clinical modules, patient data, project-specific resources, Workspace instances, Editors, or scientific libraries.

All operations must:

- Run outside the main UI thread when appropriate.
- Support cancellation where practical.
- Avoid competing with user-initiated operations.
- Report failures without making the HomePage unusable.

Background initialization should remain limited and demand-driven. It must not become a speculative resource-preloading system.

### 3.4 Project/Workflow Activation

Project/Workflow Activation begins only after an explicit user request to open a project or activate a workflow.

This is the first stage in which clinical resources may be initialized.

Responsibilities include:

1. Validate the activation request.
2. Resolve project and workflow requirements.
3. Load the project configuration and required metadata.
4. Resolve module and service dependencies.
5. Initialize the Workspace shell.
6. Construct required Editors and placeholders.
7. Activate required module implementations.
8. Initialize the necessary Tools, Commands, Services, and Capabilities.
9. Load clinical data and scientific dependencies as required.
10. Present the functional workflow.

Only resources required by the selected workflow should be activated. Other modules and scientific dependencies remain unloaded.

## 4. Application Boot Sequence

The composition root coordinates the initial startup process.

A simplified sequence is:

```text
Application Entry Point
    |
    v
Load Essential Configuration
    |
    v
Initialize Basic Logging
    |
    v
Create QApplication
    |
    v
Initialize Essential Application Paths
    |
    v
Create Minimum Shared Services
    |
    v
Construct MainWindow
    |
    v
Initialize HomePage
    |
    v
Present MainWindow
    |
    v
Confirm HomePage Readiness
    |
    v
Start Background Initialization
```

The composition root is responsible for assembling dependencies and defining their lifecycle.

It should not become a container for feature-specific initialization logic.

### 4.1 Critical Path

The critical path includes only operations required to present a functional HomePage.

Non-essential operations must be moved outside this path whenever possible.

In particular:

- Module discovery must use lightweight manifests.
- Registry construction must not instantiate module implementations.
- Editor registration must not import heavy Editor dependencies.
- Flow discovery must not load workflow implementations.
- Project discovery must use indexed metadata rather than exhaustive filesystem traversal.

The application should avoid importing VTK, ITK, PyDICOM, OCCT, SciPy, CuPy, or similar libraries during the critical path unless a genuine application-level requirement is established.

## 5. HomePage Readiness

Calling `MainWindow.show()` does not guarantee that the interface has completed its first paint or become responsive.

HomePage readiness should be treated as an explicit lifecycle milestone.

Background Initialization must begin only after the initial interface has been presented and the event loop has had an opportunity to process the initial rendering and input events.

The readiness mechanism should avoid arbitrary delays and should not depend on a fixed startup timer.

The HomePage must remain responsive while secondary resources are prepared.

## 6. Splash Screen and Startup Feedback

A splash screen is optional.

It should be introduced only when measured startup behavior justifies it.

If implemented:

- Create `QApplication` before `QSplashScreen`.
- Keep the splash screen lightweight.
- Display meaningful initialization stages.
- Avoid artificial progress indicators.
- Do not load additional resources solely to populate the splash screen.
- Close it when the HomePage is ready to be presented.

For short startup sequences, presenting the HomePage directly is preferable.

## 7. Lazy Loading and Resource Registration

### 7.1 Module Discovery

Module discovery must be lightweight.

Module manifests may declare:

- Module identifier.
- Display metadata.
- Version.
- Declared dependencies.
- Available capabilities.
- Implementation references.

Registering a manifest must not import or instantiate the complete module implementation.

### 7.2 Registry Design

Registries should store metadata and implementation references.

Implementation resolution occurs only when the corresponding resource is required.

This applies to:

- ModuleRegistry.
- EditorRegistry.
- ToolRegistry.
- FlowCatalog.
- Service registries.

Avoid eager imports in package `__init__.py` files and application entry points.

### 7.3 Editor Shells and Implementations

Workspace construction should be independent of heavy Editor implementations whenever possible.

Distinguish between:

- **Workspace shell:** structural layout and Area containers.
- **Editor shell:** lightweight UI representation or placeholder.
- **Editor implementation:** functional Editor and its feature-specific dependencies.

The Workspace shell and required Editor placeholders may be constructed before heavy module implementations finish initializing.

An Editor must not be presented as fully available until its required implementation and dependencies are ready.

## 8. Project and Workflow Activation

### 8.1 Activation Lifecycle

Project/Workflow Activation should be managed as an explicit lifecycle operation.

A typical sequence:

```text
Activation Request
    |
    v
Validate Project and Workflow
    |
    v
Resolve Requirements and Dependencies
    |
    v
Create Activation Context
    |
    v
Construct Workspace Shell
    |
    v
Create Editor Shells / Placeholders
    |
    v
Initialize Required Implementations
    |
    v
Load Required Clinical Resources
    |
    v
Mark Components Ready
    |
    v
Present Functional Workspace
```

The activation process should expose meaningful states, such as:

- `PENDING`
- `INITIALIZING`
- `READY`
- `FAILED`

A component must not be marked `READY` before its required dependencies are available.

### 8.2 Incremental Activation

Only resources required by the selected workflow should be activated.

For example, a tomography-based workflow may require VTK, image processing, and DICOM support, while another workflow may require a different dependency set.

Dependencies shared between modules should be initialized once and reused where appropriate.

The existence of a dependency relationship must not automatically force unrelated modules or implementations to load.

### 8.3 Activation Failure and Rollback

Activation must provide a controlled failure path.

If initialization fails:

1. Stop or cancel activation tasks when possible.
2. Prevent incomplete components from being exposed as ready.
3. Release partially initialized resources.
4. Dispose of the incomplete Workspace and Editor instances.
5. Restore the previous navigation state.
6. Return the user to the HomePage.
7. Present an actionable error message.
8. Preserve the usability of the application.

Rollback must account for shared resources. A resource already in use by another active component must not be released merely because one activation failed.

The activation process should be designed to avoid partially committed application state.

## 9. Background Task Management

Long-running operations must not block the main UI thread.

Use the application task infrastructure for operations such as:

- Project index reconciliation.
- Optional metadata retrieval.
- Module activation.
- Clinical data loading.
- Scientific processing.

Task management should provide:

- Explicit task states.
- Progress reporting where meaningful.
- Cooperative cancellation.
- Error propagation.
- Dependency tracking.
- Controlled resource usage.

Not every operation requires a separate thread. Lightweight operations should remain simple, while CPU-intensive or I/O-intensive tasks should use suitable execution mechanisms.

Qt-based workers may use `QThreadPool` and `QRunnable` where appropriate.

Scientific libraries must be evaluated individually for thread-safety and concurrency constraints.

## 10. Error Handling

Errors should be handled according to their impact.

| Error category | Expected behavior |
|---|---|
| Essential boot failure | Abort startup with an actionable error. |
| HomePage initialization failure | Prevent presentation of an unusable HomePage and report the failure. |
| Secondary background failure | Log the error and preserve application usability. |
| Project index failure | Attempt controlled recovery without compromising project data. |
| Project/workflow activation failure | Roll back activation and restore the HomePage. |
| Clinical resource failure | Report the affected functionality and prevent invalid operations. |

Errors should include sufficient diagnostic context without exposing patient information or sensitive project data.

## 11. Application Shutdown

Application shutdown must follow the lifecycle and ownership rules defined in **ADR-0011**.

The application lifecycle owner is responsible for coordinating shutdown. Individual UI components must not independently terminate shared application infrastructure.

The shutdown sequence must respect the dependency order and task lifecycle defined by ADR-0011.

At a minimum, the implementation must ensure that:

- New background work is no longer accepted when shutdown begins.
- Pending tasks are handled according to their lifecycle contract.
- Running tasks are handled according to their cancellation contract.
- Shared resources remain available until their dependent operations have completed.
- Resources are released in the appropriate dependency order.
- Logging and telemetry are flushed when applicable.
- The process does not leave partially persisted application state.

Task cancellation must be cooperative wherever required by the underlying operation. The application must not assume that arbitrary Python or native-library work can be safely interrupted.

Shutdown must use the task-management contract established by ADR-0011, including its defined waiting and timeout behavior. This document does not redefine that contract.

The application entry point must guarantee the shutdown procedure through a controlled lifecycle boundary, such as `try/finally`, while preserving the ownership responsibilities established by the architecture.

## 12. Performance and Instrumentation

Startup performance must be measured rather than inferred.

Relevant milestones include:

- Process start.
- Configuration loaded.
- Logging initialized.
- `QApplication` created.
- Essential paths initialized.
- Shared services initialized.
- `MainWindow` constructed.
- HomePage constructed.
- MainWindow shown.
- First paint.
- HomePage ready.
- Background Initialization started and completed.
- Project activation requested.
- Workspace shell ready.
- Required Editors ready.
- Workflow ready.

Use `time.perf_counter_ns()` for high-resolution timing.

Python import overhead can be investigated with:

```bash
python -X importtime -m cranioz
```

Instrumentation should distinguish:

- Application startup latency.
- HomePage readiness latency.
- Project activation latency.
- Workflow readiness latency.
- Resource initialization time.
- Background task overhead.
- Memory consumption.

Performance targets must be established through benchmarks on representative hardware.

The primary user-facing metric is the time required to reach a functional state, not merely the time until the process starts.

Optimization should target measured bottlenecks rather than introduce predictive or speculative initialization mechanisms.

## 13. Testing

Startup behavior should be covered by automated tests.

### 13.1 Boot Tests

- Essential configuration is loaded.
- Required infrastructure is initialized.
- Clinical modules are not imported.
- Scientific libraries are not imported unnecessarily.
- MainWindow can be constructed with controlled dependencies.

### 13.2 HomePage Tests

- Required HomePage resources are available.
- Project metadata is retrieved without opening project contents.
- Project discovery does not require a full filesystem scan on every startup.
- The HomePage becomes usable before Background Initialization begins.
- Missing or corrupted indexes are handled safely.

### 13.3 Background Initialization Tests

- Secondary tasks do not block the UI.
- Task failures do not compromise the HomePage.
- Background operations can be cancelled when appropriate.
- Operations do not interfere with user-initiated tasks.

### 13.4 Activation Tests

- Required dependencies are resolved.
- Workspace shells can be constructed independently of heavy implementations.
- Components transition through valid lifecycle states.
- Failed activation performs rollback.
- Shared resources are not released prematurely.
- The HomePage remains accessible after activation failure.

### 13.5 Shutdown Tests

- Shutdown follows ADR-0011.
- Pending tasks are handled correctly.
- Running tasks respect their cancellation contracts.
- Shared resources are released in dependency order.
- Persistence and logging are finalized appropriately.

## 14. Architectural Constraints

The following constraints are mandatory:

1. Application Boot must remain independent of clinical modules.
2. HomePage Initialization must not load project or patient contents.
3. Background Initialization must remain limited to secondary, non-clinical resources.
4. Clinical resources must only be activated after an explicit Project/Workflow Activation request.
5. Module and Editor registration must not require eager implementation imports.
6. Workspace shells and Editor placeholders must be separable from heavy implementations.
7. Background operations must not compromise UI responsiveness.
8. Activation failures must have a controlled rollback path.
9. Shutdown must follow ADR-0011.
10. Performance optimization must be based on measured bottlenecks.

## 15. Future Considerations

Potential improvements should be evaluated individually and introduced only when justified by measured performance or usability requirements.

Examples include:

- More efficient project indexing.
- Improved activation diagnostics.
- Incremental loading of large project metadata.
- Better visibility into initialization bottlenecks.
- Resource-specific performance optimizations.

The startup architecture should remain deterministic and straightforward.

**Load only what is required, when it is required.**