# CranioZ Configuration & Settings

## 1. Overview

CranioZ configuration defines application behavior, user preferences, visualization defaults, processing policies, and contextual settings.

Configuration management is independent of UI presentation. Settings are defined, validated, resolved, applied, and persisted through a centralized configuration system. UI components provide access to these settings without owning their definitions or persistence logic.

The system supports multiple configuration scopes, contextual resolution, temporary previews, controlled application policies, and versioned persistence.

### Design Principles

- Centralized configuration management.
- Separation between configuration logic, persistence, and UI.
- Explicit configuration scopes and ownership.
- Context-aware value resolution.
- Reusable settings interfaces.
- Versioned schemas and deterministic migrations.
- Safe validation, application, and persistence.
- Clinical reproducibility and traceability.
- Minimal architectural complexity.

---

## 2. Configuration Architecture

The configuration system consists of four main responsibilities.

### 2.1 Application Bootstrap

Application Bootstrap loads the essential configuration required to initialize CranioZ.

It initializes the configuration infrastructure before constructing the remaining application components.

Only startup-critical settings should be loaded at this stage. Project-, Study-, Module-, and Extension-specific configuration is loaded when the corresponding context becomes available.

### 2.2 Configuration Manager

`ConfigurationManager` is the central interface for configuration operations.

It is responsible for:

- Registering and discovering setting definitions.
- Providing setting metadata and current values.
- Resolving effective values across supported scopes.
- Validating configuration changes.
- Managing pending changes and temporary previews.
- Coordinating commits and persistence.
- Applying configuration policies.
- Notifying affected components of committed changes.
- Restoring defaults within the appropriate scope.

The manager uses the existing configuration infrastructure rather than duplicating its responsibilities.

### 2.3 Configuration Stores

Configuration Stores provide persistence adapters for the scopes that require separate storage.

They should remain lightweight and reuse the existing configuration loader, schema, and migration infrastructure.

### 2.4 Configuration Views

Configuration Views present settings through reusable UI components.

They retrieve definitions and values from `ConfigurationManager`, display the appropriate controls, and forward user changes.

They do not own configuration schemas, resolution rules, or persistence.

---

## 3. Configuration Context

Configuration resolution requires an explicit context. The manager must not infer Project, Study, Module, or Extension context from global application state.

Use an immutable `ConfigurationContext`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigurationContext:
    application_id: str
    project_id: str | None = None
    study_id: str | None = None
    module_id: str | None = None
    extension_id: str | None = None
```

Example:

```python
value = configuration_manager.get(
    "measurement.precision",
    context=study_context,
)
```

Context fields have distinct purposes:

- `application_id`: identifies the application instance.
- `project_id`: identifies the Project persistence context.
- `study_id`: identifies the Study persistence context.
- `module_id`: identifies the requesting or owning Module.
- `extension_id`: identifies the requesting or owning Extension.

Project and Study identifiers determine contextual persistence. Module and Extension identifiers identify ownership or the requesting component; they do not automatically determine the configuration scope.

The application lifecycle creates and supplies contexts to components that require them. Context should not be passed indiscriminately through every function.

The manager must validate the supplied context before reading or writing contextual settings. Missing context must never cause accidental access to another Project or Study.

---

## 4. Configuration Scopes

Each setting declares the scopes in which it can be stored.

| Scope | Purpose | Persistence |
|---|---|---|
| Application | User-wide preferences | User configuration directory |
| Machine | Hardware and local environment preferences | Machine-local configuration |
| Project | Project-specific configuration | Project directory |
| Study | Study-specific configuration | Within the Project |
| Module | Module-owned configuration | Associated supported scope |
| Extension | Extension-owned configuration | Associated supported scope |

Module and Extension identify ownership. Their settings may be stored at Application, Project, or Study scope when supported by their definitions.

### 4.1 Resolution Precedence

For settings that support contextual overrides:

`Study → Project → Application → Schema Default`

Machine-local settings are resolved separately and cannot be overridden by Project or Study configuration.

Not every setting supports every scope. The manager must enforce the scopes declared by each setting definition.

### 4.2 Application Defaults

Application preferences provide defaults for newly created Projects and Studies.

Changing an Application preference must not overwrite an explicitly stored Project or Study value.

### 4.3 Machine-Local Settings

Hardware and environment settings must remain local and must not be included in Project exports or synchronization.

Examples include:

- GPU selection.
- Maximum processing threads.
- Memory limits.
- Cache locations.
- Temporary file locations.

These settings may be represented by `machine_local=True` in their definitions.

### 4.4 Clinical Reproducibility

Settings that affect clinical interpretation, quantitative results, or planning reproducibility may require a snapshot when a Project or Study is created.

Use metadata such as:

```python
snapshot_on_create = True
```

Examples include:

- Measurement units and precision.
- Orientation conventions.
- Quantitative analysis parameters.
- Reference presets used in an analysis.

The effective value is copied into the relevant Project or Study context. Subsequent changes to global preferences must not silently alter the snapshot.

Changes to reproducibility-sensitive settings should be traceable through a separate audit record containing the setting ID, previous value, new value, timestamp, and relevant context.

Presentation-only settings can normally inherit global preferences.

---

## 5. Configuration Definitions

Every setting must have a registered definition.

A definition should include:

| Property | Description |
|---|---|
| `id` | Unique setting identifier |
| `owner_id` | Identifier of the owning component |
| `owner_type` | Core, Module, or Extension |
| `data_type` | Expected value type |
| `default` | Default value |
| `allowed_scopes` | Supported persistence scopes |
| `validation` | Constraints and validation rules |
| `application_policy` | How changes are applied |
| `machine_local` | Whether the setting is machine-specific |
| `snapshot_on_create` | Whether the value is copied into new clinical contexts |
| `metadata` | Optional description, category, UI hints, and related information |

Definitions are registered by their owners.

- Core defines and maintains core settings.
- Modules define and maintain their own settings.
- Extensions define and maintain their own settings.

Setting identifiers must be stable and globally unique. Renaming or removing an identifier requires an explicit migration strategy.

---

## 6. Configuration Organization

```text
SETTINGS
│
├── APPLICATION
│   │
│   ├── General
│   │   ├── Startup
│   │   │   ├── Startup Behavior
│   │   │   ├── Restore Previous Session
│   │   │   └── Default Startup Page
│   │   │
│   │   ├── Storage
│   │   │   ├── Default Project Location
│   │   │   ├── Default Data Location
│   │   │   └── Temporary Files Location
│   │   │
│   │   ├── Saving & Recovery
│   │   │   ├── Auto Save
│   │   │   ├── Auto Save Interval
│   │   │   ├── Recovery Options
│   │   │   └── Undo/Redo History Limit
│   │   │
│   │   ├── Notifications
│   │   └── Updates
│   │       ├── Automatic Update Check
│   │       └── Update Channel
│   │
│   ├── Appearance
│   │   ├── Theme
│   │   │   ├── Color Theme
│   │   │   ├── Color Scheme
│   │   │   └── Window Opacity
│   │   ├── Typography
│   │   │   ├── Font Family
│   │   │   └── Font Size
│   │   └── Icons
│   │
│   ├── Interface
│   │   ├── Homepage
│   │   ├── Toolbars
│   │   └── Dialogs
│   │
│   ├── Workspace
│   │   ├── Central Area
│   │   ├── Left Area
│   │   ├── Right Area
│   │   └── Bottom Area
│   │
│   ├── Accessibility
│   │   ├── Text Scaling
│   │   ├── Contrast
│   │   └── Motion
│   │
│   ├── Language & Region
│   │   ├── Language
│   │   ├── Regional Format
│   │   ├── Measurement Units
│   │   ├── Number Format
│   │   └── Date & Time Format
│   │
│   ├── Shortcuts
│   │   ├── Keyboard Bindings
│   │   ├── Shortcut Customization
│   │   ├── Conflict Detection
│   │   ├── Import / Export
│   │   └── Restore Defaults
│   │
│   └── Artificial Intelligence
│       ├── AI Providers
│       ├── Models
│       ├── Processing Preferences
│       └── Privacy
│
├── MEDICAL DATA VISUALIZATION
│   │
│   ├── Annotations
│   │   ├── Colors
│   │   ├── Fonts
│   │   ├── Line Thickness
│   │   └── Visibility
│   │
│   ├── DICOM 2D
│   │   ├── Window/Level
│   │   ├── Slice Orientation
│   │   ├── Slice Presentation
│   │   └── Crosshair
│   │
│   ├── Volume Rendering
│   │   ├── Default Presets
│   │   ├── Rendering Quality
│   │   └── Opacity
│   │
│   ├── 3D Models
│   │   ├── Default Colors
│   │   ├── Lighting
│   │   ├── Surface Representation
│   │   └── Transparency
│   │
│   ├── Measurements
│   │   ├── Precision
│   │   ├── Colors
│   │   ├── Labels
│   │   └── Visibility
│   │
│   └── Cephalometric Points
│       ├── Colors
│       ├── Point Size
│       ├── Labels
│       └── Visibility
│
├── LIBRARY
│   │
│   ├── Asset Libraries
│   │   ├── Library Locations
│   │   ├── Add / Remove Libraries
│   │   ├── Enable / Disable Libraries
│   │   └── Refresh Libraries
│   │
│   └── Installed Packages
│       ├── Installed Packages
│       ├── Package Versions
│       ├── Updates
│       └── Remove Packages
│
├── PERFORMANCE
│   │
│   └── Processing
│       ├── CPU
│       │   ├── Multithreading
│       │   ├── Maximum Threads
│       │   └── Processing Parallelism
│       │
│       ├── GPU
│       │   ├── GPU Selection
│       │   ├── Hardware Acceleration
│       │   └── GPU Memory
│       │
│       ├── Memory
│       │   ├── Memory Limits
│       │   └── Memory Management
│       │
│       ├── Cache
│       │   ├── Cache Location
│       │   ├── Maximum Cache Size
│       │   └── Cache Management
│       │
│       └── Background Processing
│           ├── Concurrent Tasks
│           └── Task Priorities
│
├── MODULES
│   │
│   ├── Module Management
│   │   ├── Installed Modules
│   │   ├── Enable / Disable Modules
│   │   └── Module Information
│   │
│   └── Module Settings
│       ├── Tomography
│       ├── Cephalometry
│       ├── Orthognathic Surgery
│       ├── TMJ
│       └── ...
│
└── EXTERNAL RESOURCES
    │
    ├── Extensions
    │   ├── Installed Extensions
    │   ├── Extension Repositories
    │   ├── Updates
    │   └── Dependencies
    │
    └── Integrations
        ├── External Services
        ├── Data Sources
        └── Connections
```

Project and Study settings are displayed contextually when their respective contexts are available. They are not permanent global navigation categories.

Module and Extension settings are discovered dynamically from their registered definitions.

---

## 7. Configuration Views

The configuration UI uses a shared `ConfigurationView` hosted in two different application contexts.

### 7.1 Homepage: Preferences Window

The Preferences Window is available before a Project is opened.

It provides access to:

- Application settings.
- Machine-local settings.
- Discoverable Module and Extension settings.
- Other globally available configuration definitions.

It is a standalone modal window, not a Workspace Editor.

Actions:

- **OK**: commit pending changes and close.
- **Cancel**: discard pending changes, revert previews, and close.
- **Apply**: commit pending changes without closing.

### 7.2 Workspace: Settings Editor

The Settings Editor is hosted in a Workspace Area and is available when a Project is open.

It provides access to:

- Application settings.
- Machine-local settings.
- Project settings.
- Study settings when a Study context is available.
- Module and Extension settings.

The Settings Editor may be opened without a selected clinical object or active Study. Project-level settings remain accessible.

Actions:

- **Apply**: commit pending changes.
- **Revert**: discard pending changes and revert previews.

It does not require an OK action because it remains embedded in the Workspace.

### 7.3 Shared View

Both hosts reuse the same `ConfigurationView`, including:

- Navigation and categories.
- Search.
- Setting panels.
- Reusable controls.
- Validation feedback.
- Contextual setting information.

The host owns its window or Area integration and transaction controls. The shared View does not need to know whether it is displayed modally or inside the Workspace.

The outer layouts may differ when required by their host contexts.

---

## 8. Module and Extension Settings

Module and Extension configuration must be discoverable independently of full module activation.

The settings interface distinguishes three states:

| Component state | Configuration behavior |
|---|---|
| Active | Normal display and editing |
| Inactive but available | Standard settings remain editable; specialized controls may be loaded on demand |
| Unavailable or incompatible | Display availability information and prevent invalid editing |

An inactive Module should not need to initialize its complete clinical workflow merely to expose its settings.

Standard controls can be provided directly from setting metadata. Specialized controls may be loaded through their owning component without activating the entire Module.

For example, Cephalometric Point appearance settings can remain editable even when the Cephalometry Module is inactive.

Extensions follow the same principles, subject to compatibility and security restrictions.

---

## 9. Loading and Lifecycle

Configuration loading follows the application lifecycle.

1. Bootstrap loads startup-critical Application and Machine settings.
2. Core configuration definitions are registered.
3. `ConfigurationManager` becomes available.
4. Module and Extension definitions are discovered.
5. Application and Machine configuration values are loaded and validated.
6. When a Project opens, its configuration is loaded and resolved.
7. When a Study becomes available, Study configuration is loaded.
8. Contextual values are resolved when requested.
9. Committed changes notify affected components through the existing Core event mechanism.

Configuration loading must not require UI initialization.

The manager should not poll components for changes. Notifications are event-driven.

---

## 10. Applying Configuration Changes

Every setting declares an application policy.

| Policy | Behavior |
|---|---|
| `PREVIEW` | Temporarily applied and reverted on Cancel or Revert unless committed |
| `IMMEDIATE` | Validated, committed, persisted, and applied immediately |
| `DEFERRED` | Committed and persisted now; applied at the next relevant operation |
| `RESTART_REQUIRED` | Committed and persisted; applied after application restart |

By default, changes remain pending until Apply or OK, except for settings explicitly declared `PREVIEW` or `IMMEDIATE`.

### 10.1 Hardware-Dependent Policies

Application policies must reflect the lifecycle of the affected resource.

Examples:

| Setting | Typical policy |
|---|---|
| Maximum Threads | `DEFERRED` |
| Processing Parallelism | `DEFERRED` |
| GPU Selection | `DEFERRED` or `RESTART_REQUIRED` |
| Hardware Acceleration | `DEFERRED` or `RESTART_REQUIRED` |
| GPU Memory Limit | `DEFERRED` |
| Cache Location | `DEFERRED` |
| Maximum Cache Size | `DEFERRED` |
| Memory Management | `DEFERRED` |

The policy depends on whether the affected subsystem can be safely reconfigured.

For example, GPU selection may require application restart if the rendering context cannot be safely recreated. If the context can be recreated safely, deferred application may be sufficient.

Resources must never be reconfigured while they are in unsafe active use.

### 10.2 Validation

Each setting is validated against its definition before it can be committed.

- Invalid values are rejected.
- The affected control displays a clear validation message.
- Valid independent changes remain pending.
- Dependent settings are validated as a group.

Validation must occur before persistence or application.

### 10.3 Atomic Changes

Independent settings may be committed separately.

Dependent settings must be grouped into an atomic change set:

1. Validate the complete group.
2. Prepare the new configuration state.
3. Persist the group.
4. Apply the changes according to their policies.
5. Notify affected components.

A failed validation or persistence operation must preserve the previous committed state. The system must not leave a partially committed dependent configuration group.

### 10.4 Restore Defaults

Restore Defaults operates within an explicit context and scope.

It may target:

- A setting.
- A panel.
- A category.
- A selected configuration scope.

Restored values remain pending until committed, except for settings using `IMMEDIATE`.

Restoration must respect setting ownership, supported scopes, and clinical snapshot requirements.

### 10.5 Undo/Redo and Audit

Configuration changes do not use the clinical `CommandExecutor` or Project Undo/Redo stack.

Configuration transaction handling and clinical command history are separate concerns.

Reproducibility-sensitive changes may generate audit records independently of Undo/Redo.

---

## 11. Persistence, Versioning, and Migration

Configuration persistence reuses the existing infrastructure:

| Component | Responsibility |
|---|---|
| `config/loader.py` | Loading and serialization |
| `config/schema.py` | Definitions, schemas, and validation |
| `config/migration.py` | Versioned migrations |
| `settings/preferences.py` | Application preference integration |

`ConfigurationManager` coordinates these components without duplicating their responsibilities.

### 11.1 Persistence Locations

| Scope | Location |
|---|---|
| Application | User configuration directory |
| Machine | Machine-local configuration directory |
| Project | Project directory, following ADR-0009 |
| Study | Study data within the Project |
| Module / Extension | Associated supported persistence scope |

Machine-local settings must not be included in Project exports.

### 11.2 Schema Versioning

Every persisted configuration set must identify its owner and schema version.

Example:

```json
{
  "owner_id": "cranioz.tmj",
  "schema_version": 2,
  "values": {
    "rendering.condyle_color": "#D9A441",
    "rendering.surface_opacity": 0.85
  }
}
```

Application, Machine, Project, Study, Module, and Extension configuration formats must be versioned according to their persistence lifecycle.

The Project configuration format must remain consistent with ADR-0009.

### 11.3 Migration Contract

Migrations are deterministic, versioned, and independent of UI components.

- Core maintains migrations for Core-owned configuration.
- Modules and Extensions provide migrations for their own configuration schemas.
- Incompatible schema changes require an explicit migration.
- Unknown values must not be silently discarded.
- Migration failures must preserve the original data.
- Migration must not depend on an active UI or clinical workflow.

Existing `config/migration.py` should support these operations. A separate migration engine is unnecessary.

### 11.4 Downgrade Safety

Migrations are generally forward-only. Full reversibility must not be assumed.

Before migration:

- Preserve the original configuration or create a recoverable backup.
- Validate the target schema and migration path.
- Avoid destructive transformations without a defined recovery strategy.

If an older application version cannot interpret a newer schema safely, it must not silently rewrite or discard the data. Recovery should use the preserved backup or report the incompatibility.

Third-party Extension migrations require restricted execution and must not receive unrestricted access to application or patient data.

---

## 12. Security and Sensitive Configuration

Sensitive credentials must not be stored in ordinary configuration files.

Use the operating system's secure credential storage when available:

- Windows Credential Manager.
- macOS Keychain.
- Linux Secret Service / libsecret.

AI provider API keys and other credentials must never be written to ordinary JSON files, Project exports, or application logs.

Configuration files may store references to credentials held in the secure store.

### 12.1 AI Privacy and Consent

AI provider configuration and patient data-sharing consent are separate mechanisms.

Configuring an API key or enabling an AI provider does not authorize patient data transmission.

Before identifiable patient data is sent externally, explicit authorization must identify:

- Destination provider.
- Data to be transmitted.
- Purpose of processing.

Without the required authorization, identifiable patient data transmission must be blocked.

Consent and related authorization events must be handled and audited according to applicable privacy requirements.

---

## 13. Design Requirements

The configuration system must satisfy the following requirements:

- Configuration definitions are independent of UI components.
- All configuration access goes through `ConfigurationManager`.
- Every setting has a stable identifier and explicit owner.
- Every setting declares supported scopes and validation rules.
- Contextual resolution is explicit and centralized.
- Machine-local settings cannot be overridden by Project or Study values.
- Application defaults do not overwrite explicit contextual values.
- Clinical reproducibility-sensitive values support contextual snapshots.
- Inactive Modules and Extensions remain discoverable when their definitions are available.
- Configuration schemas and persisted data are versioned.
- Migrations are deterministic and preserve original data on failure.
- Dependent changes are committed atomically.
- Application policies prevent unsafe resource reconfiguration.
- Committed changes notify affected components through Core events.
- Configuration changes remain separate from clinical Undo/Redo.
- Sensitive credentials use secure operating-system storage.
- Patient data transmission requires explicit authorization.

---

## 14. Architectural Principles

1. **Separation of concerns** — configuration logic, persistence, and presentation remain independent.
2. **Centralized management** — `ConfigurationManager` owns resolution, validation, transactions, and coordination.
3. **Explicit context** — Project, Study, Module, and Extension context is supplied rather than inferred.
4. **Scope awareness** — settings are persisted only in supported scopes.
5. **Ownership** — Core, Modules, and Extensions maintain their own definitions and migrations.
6. **Reproducibility** — clinically relevant configuration can be captured in Project and Study snapshots.
7. **Safe application** — changes respect validation, dependencies, and resource lifecycles.
8. **Versioned persistence** — configuration data remains identifiable and migratable across releases.
9. **UI independence** — Preferences and Settings Editor share presentation components without sharing host responsibilities.
10. **Minimal complexity** — reuse existing infrastructure and introduce additional abstractions only when required.