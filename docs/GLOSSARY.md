# CranioZ Glossary

**Document type:** Reference
**Status:** Living document
**Scope:** Canonical definitions of terms used across the CranioZ documentation

---

## 1. Purpose

This glossary provides a single, authoritative definition for each term used in the CranioZ architecture and design documentation.

It exists to:

- Eliminate ambiguity when the same term appears in multiple documents.
- Provide a canonical reference for contributors and reviewers.
- Distinguish terms that are easily confused (e.g., *Area* vs. *Editor*, *Tool* vs. *Command*, *Datatype* vs. *Semantic Type*).
- Link each term to the document(s) that define its detailed contract.

**Rule:** when a document uses a term defined here, it should use it with the meaning given here. If a document needs a different meaning, it must declare that explicitly and link back to this glossary.

---

## 2. How to Use This Glossary

- **Definitions here are normative.** A document may expand a definition, but it must not contradict it.
- **Terms are grouped by domain** (Architecture, UI, Domain, Application, etc.) for navigability.
- **Cross-references** point to the document(s) that specify the term in detail.
- **Aliases and deprecated terms** are listed explicitly to prevent their reintroduction.

If a term is missing, add it here first, then reference it from the relevant document.

---

## 3. Architectural Terms

### ADR — Architecture Decision Record
A document that records a significant architectural decision, its context, alternatives considered, and consequences. CranioZ ADRs live under `docs/adr/` and follow a numbered convention (`ADR-0001`, `ADR-0002`, ...).

**See:** `docs/adr/`

### Application Layer
The layer that coordinates system operations: Commands, Services, Tasks, Flows, Events, transactions, and application-level state. It orchestrates the Domain and Infrastructure layers.

**See:** `docs/architecture/overview.md` §5.2

### Capability
An operational capability that can be applied to an Object, resolved by the system from the Object's Datatype, Semantic Type, Components, and context. Capabilities are not statically stored on the Object.

**Distinguish from:** *Tool* (a user-facing interaction), *Component* (data/structure the Object has).

**See:** `docs/architecture/objects/objects.md` §5

### Command
An executable application operation. Every persistent state-changing operation in CranioZ passes through the Command mechanism, which provides validation, transaction boundaries, undo/redo, event publication, and auditability.

**Distinguish from:** *Tool* (an interaction interface that may produce a Command), *Service* (reusable functionality).

**See:** `docs/architecture/commands/commands.md`

### Component
Additional information or structure associated with an Object (e.g., `Transform`, `LandmarkSet`, `AnatomicalProperties`). A Component answers "What does the Object have?"

**Distinguish from:** *Capability* ("What can be done with the Object?").

**See:** `docs/architecture/objects/objects.md` §4

### Datatype
The fundamental structure of the data manipulated by CranioZ (e.g., `Mesh`, `Volume`, `Image2D`, `Curve`, `Point`, `PointCloud`, `ROI`). A Datatype does not, by itself, define clinical meaning.

**Distinguish from:** *Semantic Type* (what the data represents).

**See:** `docs/architecture/objects/datatypes.md`

### Domain Layer
The layer that contains the conceptual model: Patient, Project, Scene, Object, Datatype, Semantic Type, Component, Capability, and clinical rules. It is independent of Qt, VTK, filesystem, and any infrastructure concern.

**See:** `docs/architecture/overview.md` §5.1`

### Flow
A versioned, declarative sequence of steps that guides a user through a clinical task by coordinating steps, requirements, and modules. Flow definitions are stored as JSON; the execution engine belongs to the Application layer.

**See:** `docs/architecture/clinical_workflows/clinical_workflows.md`

### Infrastructure Layer
The layer that contains technical implementations: DICOM access, VTK/ITK integration, file I/O, persistence, and external library adapters. It implements the ports defined by the Application layer.

**See:** `docs/architecture/overview.md` §5.3`

### Module
A coherent functional capability that composes Tools, Commands, Services, Data Types, Editors, and Flows. Modules declare their UI composition via a `ModuleUISpec`; they do not own Areas or Editors.

**See:** `docs/architecture/overview.md` §6, `docs/architecture/modules/modules.md`

### Object
The entity manipulated by CranioZ, understood through four dimensions: Data (Datatype), Semantic (Semantic Type), Components, and Capabilities.

**See:** `docs/architecture/objects/objects.md`

### Plugin
An external extension that provides Modules, Tools, Services, Data Types, UI components, Flows, or Capabilities through public extension points. Plugins must use versioned public APIs, not internal implementation details.

**See:** `docs/architecture/overview.md` §17`

### Ports and Adapters
The architectural pattern used by CranioZ. The Application layer defines ports (interfaces) for persistence, project loading/saving, external computation, and rendering integration. Infrastructure provides concrete adapters.

**See:** `docs/architecture/overview.md` §16`

### Scene
The domain-level spatial organization of objects within a specific planning context. The Scene defines object membership, spatial hierarchy, transforms, reference frames, and the coordinate system. It does not own the lifecycle of domain objects.

**Distinguish from:** *DomainObjectStore* (owns canonical object identity and lifecycle), *Rendering Representation* (how it is visualized).

**See:** `docs/architecture/scene/scene.md`

### Semantic Type
The clinical meaning assigned to an Object (e.g., `Anatomy.Bone.Mandible`, `Imaging.CT`, `Surgical.Guide`). The same Datatype (e.g., `Mesh`) can carry different Semantic Types.

**Distinguish from:** *Datatype* (the structure of the data).

**See:** `docs/architecture/objects/datatypes.md`, `docs/architecture/objects/objects.md` §3

### Service
Reusable application or domain functionality not naturally belonging to a single entity. Services have explicit contracts.

**Distinguish from:** *Command* (a specific executable operation), *Tool* (a user-facing interaction).

**See:** `docs/architecture/overview.md` §9`

### Task
A potentially long-running operation managed by the Application layer, providing execution, progress, cancellation, error propagation, and result delivery.

**See:** `docs/architecture/overview.md` §9`

### Tool
An operational capability exposed to the user. A Tool defines what it represents, how it is identified, in which contexts it is available, and how interaction is initiated. Execution is delegated to Commands and Application Services.

**Distinguish from:** *Command* (the executable operation), *Widget* (a reusable UI component).

**See:** `docs/architecture/ui/tools/tools.md`

---

## 4. UI Terms

### Area
A structural container provided by the Workspace. It occupies a position in the Area Layout Tree and hosts one or more Editors, organized in its own internal Editor Layout Tree. There is no `EditorHost` — the Area manages its Editors directly.

**Distinguish from:** *Editor* (functional unit), *Region* (a geometric grouping of Areas), *Overlay* (a floating layer).

**See:** `docs/architecture/ui/workspace/workspace.md` §2, ADR-0001

### Area Layout Tree
The N-ary split tree that organizes the Areas of the Workspace. Nodes are `Leaf` (one Area) or `Split` (direction + two or more children). The Area Layout Tree is the single source of truth for Workspace structure.

**See:** `docs/architecture/ui/workspace/workspace.md` §5`

### Editor
A functional unit hosted inside an Area. It provides a specific interaction experience (e.g., `Viewport3DEditor`, `MPRViewerEditor`, `ConsoleEditor`). An Editor declares and materializes its own Toolbar(s) and internal overlays.

**Distinguish from:** *Area* (the structural container), *Tool* (an action), *Toolbar* (the presentation of Tools inside an Editor).

**See:** `docs/architecture/ui/editors/editors.md`, ADR-0001, ADR-0002

### Editor Layout Tree
The N-ary split tree internal to an Area that organizes the Editors hosted by that Area. It uses the same node types as the Area Layout Tree (`Leaf`, `Split`).

**See:** `docs/architecture/ui/workspace/workspace.md` §5`, `docs/architecture/ui/editors/editors.md` §8

### EditorCatalog
The context-aware filter over the `EditorRegistry`. It answers: "Which registered Editors can be used in the current context?" It considers the active Scene, Project, Area, and required capabilities/data.

**Distinguish from:** *EditorRegistry* (the registry of all Editor types).

**See:** `docs/architecture/ui/editors/editors.md` §6

### EditorContext
The controlled set of dependencies an Editor receives at insertion time. Created once per Editor (hybrid model): fields specific to the Editor (identity, view state, extras) are isolated; shared services (SceneQuery, CommandDispatcher, EventSubscription, EditorServices) are propagated by reference.

**See:** `docs/architecture/ui/editors/editors.md` §15, ADR-0002

### EditorRegistry
The registry of all Editor **types** known to the system. It resolves `editor_id` to concrete Editor classes and creates instances. It does **not** manage instances.

**Error contracts:** `register` raises `ValueError` on duplicate; `resolve` and `create` raise `KeyError` on unknown.

**See:** `docs/architecture/ui/editors/editors.md` §5, `docs/architecture/ui/workspace/workspace.md` §3.6

### LayoutBuilder
The component that consumes a `ModuleUISpec` and produces a `LayoutTree`. It is a **pure** composition step: it does not import PySide6, does not require a `QApplication`, and does not create widgets.

**Distinguish from:** *LayoutRenderer* (materializes widgets).

**See:** `docs/architecture/ui/workspace/workspace.md` §3.5`, ADR-0002

### LayoutRenderer
The component that materializes a `LayoutTree` as Qt widgets (nested `QSplitter` widgets and Area widgets). It is the sole materializer of widgets: Areas, Splits, Editors, and Toolbars.

**Distinguish from:** *LayoutBuilder* (pure composition step).

**See:** `docs/architecture/ui/workspace/implementation/workspace-implementation.md` Phase 6, ADR-0002

### LayoutState
The presentation state associated with a Workspace layout: proportions (`QSplitter` sizes per node), visibility (which Areas are shown or hidden), and the active Editor per Area. Stored separately from the structural trees.

**Distinguish from:** *OverlayState* (state of Overlays), *ViewStateStore* (per-Editor presentation state).

**See:** `docs/architecture/ui/workspace/workspace.md` §5.3

### MainWindow
The top-level application window. It hosts the Workspace and provides the application frame (native OS window controls and, when applicable, the OS menu bar). It does not own the Workspace layout state, clinical state, or workflow semantics.

**See:** `architecture/main_window/main_window.md`

### ModuleUISpec
The declarative specification a Module provides to the Workspace, describing which Areas it wants the Workspace to materialize, their placement, and their internal Editor Layout Trees.

**See:** `docs/architecture/ui/workspace/workspace.md` §3.5

### Overlay
A floating layer managed by the Workspace, positioned over a Region of Areas. Overlays can be moved, resized, and closed. The `steps_panel` is the primary example.

**Distinguish from:** *Top Bar* (structural component, not repositionable), *Editor internal overlay* (belongs to an Editor, not the Workspace).

**See:** `docs/architecture/ui/workspace/workspace.md` §7`

### OverlayState
The presence, configuration, and anchoring of Overlays. Stored alongside the layout trees, inside the project file.

**See:** `docs/architecture/ui/workspace/workspace.md` §5.3`, §7.6

### Placement
A semantic classification of an Area within the Workspace layout: `LEFT`, `CENTRAL`, `RIGHT`, `BOTTOM`. Placement is used to build the initial Area Layout Tree and to associate Areas with Regions. It is preserved after construction.

**See:** `docs/architecture/ui/workspace/workspace.md` §3.5`

### Region
A geometric area derived from the Area Layout Tree that groups related Areas. Overlays are positioned over Regions.

**See:** `docs/architecture/ui/workspace/workspace.md` §7.2`

### Surface
A visual background belonging to a window, panel, or overlay. CranioZ defines three surface styles: **Solid**, **Translucent**, and **Frosted Glass**.

**See:** `docs/architecture/appearance/surfaces-and-overlays.md`

### Theme
The global visual palette and styling configuration of the interface (Light, Dark, System). A theme styles interface components; it does not dictate the background of every viewport.

**See:** `docs/architecture/appearance/themes-and-design-tokens.md`

### Toolbar
A widget internal to an Editor that presents Tools to the user. A Toolbar is declared by a `ToolbarSpec` and materialized by the `LayoutRenderer` from the Editor's `toolbar_specs()`. The Workspace never hosts Toolbars; the Area never hosts Toolbars.

**See:** `docs/architecture/ui/toolbar/toolbar.md`, ADR-0002

### Top Bar
A structural component of the Workspace, fixed at the top, not repositionable or closeable. It contains three segments: Left (menu, Home, toggle Left), Center (module tabs, `+` button), Right (Extras, toggle Right, window controls).

**Distinguish from:** *Overlay* (repositionable, closeable).

**See:** `docs/architecture/ui/workspace/workspace.md` §3.3`

### Widget
A reusable interface component implementing the CranioZ visual and interaction conventions. Generic composite widgets live in `src/cranioz/ui/widgets/`. Editor-internal overlays live in `src/cranioz/ui/editors/overlays/`.

**See:** `docs/architecture/appearance/widget-system.md`, ADR-0003

### Workspace
The runtime environment where clinical work happens. It is a composition of Areas (structural containers that host Editors) and Overlays (floating layers). The Workspace manages Areas and Overlays; it does not own clinical state, Tools, Toolbars, or Module behavior.

**See:** `docs/architecture/ui/workspace/workspace.md`

---

## 5. Domain Terms

### Clinical Flow
See *Flow*.

### DomainObjectStore
The canonical registry and lifecycle authority for domain objects belonging to a Project. It is Project-scoped, not application-global.

**Distinguish from:** *Scene* (spatial organization of objects).

**See:** `docs/architecture/scene/scene.md` §4

### Patient
The person associated with clinical data in CranioZ. The Patient is composed of nine section value objects (identity, documents, filiation, address, complaint, comorbidities, medications, antecedents, habits). It is referenced by a Project; it does not own clinical data such as imaging, meshes, photographs, odontogram, or documents.

**See:** `docs/architecture/domain/patient/patient.md`, ADR-0004

### PatientSummary
A lightweight read-only projection of the Patient carrying `patient_id`, `display_name`, `birth_date`, and `sex`. Used in contexts where the full record is not needed (Project Catalog, ProjectContext, tooltips).

**See:** `docs/architecture/domain/patient/patient.md` §13

### Project
The persistent clinical container associated with a patient and one or more clinical workflows. It provides the boundary within which patient-related data, imaging, models, planning data, workflow state, metadata, and other clinical artifacts are organized.

**Distinguish from:** *Patient* (the person referenced by the Project), *ProjectContext* (the runtime representation of an opened Project).

**See:** `docs/architecture/domain/project/project.md`

### Project Catalog
A read-only discovery projection of available projects. It allows the Home Page to efficiently display and search existing projects without loading complete clinical data.

**See:** `docs/architecture/domain/project/project.md` §5`

### Project Manager
The single application-level authority for the lifecycle of a project: creation, opening, updating, closing, deletion, archival, restoration, validation, access checks, persistence coordination, and lifecycle events.

**See:** `docs/architecture/domain/project/project.md` §4`

### Project Repository
The persistence abstraction through which the Project Manager loads and stores project state. It does not decide whether a project should be created, updated, opened, or deleted.

**See:** `docs/architecture/domain/project/project.md` §12`

### Project Storage
The infrastructure responsible for the physical representation of a project (filesystem, database, institutional storage, remote storage, etc.).

**See:** `docs/architecture/domain/project/project.md` §11`

### ProjectContext
A runtime initialization snapshot created when a project is opened. It is immutable for the Workspace, contains no physical paths, and does not own the project lifecycle.

**See:** `docs/architecture/domain/project/project.md` §17`

### Scene (Domain)
See *Scene* in §3.

### Workflow
See *Flow*.

---

## 6. Application and Command Terms

### CommandBus
The mechanism through which Editors and Tools publish Commands. The CommandBus routes Commands to the appropriate CommandHandler.

**See:** `docs/architecture/commands/commands.md`

### CommandDispatcher
The interface through which an Editor or Tool dispatches Commands. Part of the `EditorContext` and `ToolContext`.

**See:** `docs/architecture/ui/editors/editors.md` §15

### CommandHandler / CommandExecutor
The component responsible for validating a Command, opening a transaction, applying changes to the Domain/Scene, committing, and publishing events.

**See:** `docs/architecture/ui/workspace/workspace.md` §3.4`

### Event Bus
The mechanism through which the Application layer publishes events after a successful commit. Events communicate state changes; they do not replace Commands.

**See:** `docs/architecture/overview.md` §13`

### SelectionService
The service through which an Editor or Tool queries and observes the current selection. Part of the `EditorContext` and `ToolContext`.

**See:** `docs/architecture/ui/editors/editors.md` §15

### SceneQuery
The read-only interface through which an Editor accesses the Scene. An Editor never receives a mutable reference to the Scene.

**See:** `docs/architecture/ui/editors/editors.md` §15

### ToolContext
A strict subset of the `EditorContext` provided to a Tool. Contains `SceneQuery`, `SelectionService`, `CommandDispatcher`, and `ToolServices`. Does not contain `EventSubscription`, `ViewStateStore`, or `EditorServices`.

**See:** `docs/architecture/ui/editors/editors.md` §15

### ViewStateStore
Per-Editor presentation state (zoom, camera, current slice, visual selection, presentation mode). It is not clinical state and not the same as `LayoutState`.

**See:** `docs/architecture/ui/editors/editors.md` §15`

---

## 7. Design System Terms

### Design Token
A named value used by the design system, representing a semantic role rather than a hard-coded component-specific value. Categories include color, typography, spacing, shape, and elevation.

**See:** `docs/architecture/appearance/themes-and-design-tokens.md`

### Frosted Glass
A translucent surface combined with blur of the content behind it. Optional presentation capability, not a requirement.

**See:** `docs/architecture/appearance/surfaces-and-overlays.md`

### Modal Focus Effect
A presentation effect that visually emphasizes an active modal dialog by reducing the visual prominence of the Workspace behind it (dimming, optionally with blur).

**Status:** Blur behind VTK renderers is experimental; dimming-only is the initial default.

**See:** `docs/architecture/appearance/modal-focus-effect.md`

### Solid Surface
An opaque surface with a theme-derived background color. Default for persistent panels, clinical forms, and information-dense dialogs.

**See:** `docs/architecture/appearance/surfaces-and-overlays.md`

### Translucent Surface
A surface with partial opacity through which the underlying content remains visible. Suitable for selected floating toolbars and compact contextual controls.

**See:** `docs/architecture/appearance/surfaces-and-overlays.md`

---

## 8. Internationalization Terms

### Catalog
A JSON file organized by language and major functional area (e.g., `translations/en/tomography.json`). Each catalog contains translation keys mapped to messages and optional descriptions.

**See:** `docs/architecture/internationalization/internationalization.md` §3

### Source Text
The mandatory English text supplied as the second positional argument to `tr()`. It provides a last-resort fallback if the translation cannot be resolved through the catalogs. The English catalog remains the authoritative source.

**See:** `docs/architecture/internationalization/internationalization.md` §5

### Translation Key
A stable semantic identifier describing meaning or intent (e.g., `tomography.segmentation.failed`). It must not depend on the displayed text or a specific UI widget.

**See:** `docs/architecture/internationalization/internationalization.md` §4

### TranslationCatalogRegistry
The component that locates, loads, and caches translation catalogs by language and functional area.

**See:** `docs/architecture/internationalization/internationalization.md` §2

### TranslationService
The component that resolves translation keys, processes message parameters and pluralization, manages the active language, applies fallback rules, and notifies the interface when the language changes.

**See:** `docs/architecture/internationalization/internationalization.md` §2

### TranslationValidator
The component that checks catalog structure, key coverage, source-text consistency, formatting parameters, and translation completeness.

**See:** `docs/architecture/internationalization/internationalization.md` §2`, §9

---

## 9. Deprecated and Retired Terms

The following terms appeared in earlier drafts and are **retired**. They must not be reintroduced.

### EditorHost
A component that was once proposed to manage a list of Editors inside an Area. **Removed by ADR-0001.** The Area manages its Editors directly via its internal Editor Layout Tree.

**Do not use.** If you encounter `EditorHost` in a document, treat it as a documentation error and correct it.

### Patient_Config_Manager
A proposed component that would independently own the patient lifecycle. **Removed by ADR-0004 and `project_pt.md` §3.** Patient lifecycle is managed through the Project Manager.

**Do not use.**

### PatientManager
A proposed application-level manager for the Patient. **Removed by ADR-0004.** There is no separate Patient lifecycle manager.

**Do not use.**

### Main Toolbar
A term that appeared in earlier drafts of `toolbar.md` to describe an application-level toolbar. In the current architecture, Toolbars are internal to Editors. The Top Bar is a structural component of the Workspace, not a "Main Toolbar".

**Do not use.** Prefer *Top Bar* for the structural component, and *Toolbar* for the Editor-internal widget.

### Panel
A term that appeared in earlier drafts. In the current architecture, there is only **Area** (structural container) and **Editor** (functional unit). A "Panel" is a semantic specialization of an Editor (`editor_kind = PANEL`), not a separate concept.

**Do not use as a structural term.** If needed, refer to an Editor whose kind is `PANEL`.

---

## 10. Cross-Reference Index

| Term | Primary Document | Related ADR |
|---|---|---|
| Area | `workspace.md` §2 | ADR-0001 |
| Area Layout Tree | `workspace.md` §5 | — |
| Capability | `objects.md` §5 | — |
| Command | `commands.md` | — |
| Component | `objects.md` §4 | — |
| Datatype | `datatypes.md` | — |
| Editor | `editors.md` | ADR-0001, ADR-0002 |
| EditorCatalog | `editors.md` §6 | — |
| EditorContext | `editors.md` §15 | ADR-0002 |
| EditorRegistry | `editors.md` §5 | ADR-0002 |
| Flow | `clinical_workflows.md` | — |
| LayoutBuilder | `workspace.md` §3.5 | ADR-0002 |
| LayoutRenderer | `workspace-implementation.md` Phase 6 | ADR-0002 |
| Module | `overview.md` §6 | — |
| Object | `objects.md` | — |
| Overlay | `workspace.md` §7 | — |
| Patient | `patient.md` | ADR-0004 |
| Project | `project.md` | — |
| ProjectContext | `project.md` §17 | — |
| Scene | `scene.md` | — |
| Semantic Type | `datatypes.md`, `objects.md` §3 | — |
| Service | `overview.md` §9 | — |
| Surface | `surfaces-and-overlays.md` | — |
| Theme | `themes-and-design-tokens.md` | — |
| Tool | `tools.md` | — |
| Toolbar | `toolbar.md` | ADR-0002 |
| Top Bar | `workspace.md` §3.3 | — |
| Widget | `widget-system.md` | ADR-0003 |
| Workspace | `workspace.md` | — |

---

## 11. Maintenance

This glossary is a **living document**. When a new term is introduced in a specification:

1. Add it to the appropriate section here.
2. Cross-reference it from the document that defines it in detail.
3. If the term replaces a deprecated term, add the deprecated term to §9.

When a term's meaning changes:

1. Update the definition here **first**.
2. Update every document that uses the term.
3. Record the change in the CHANGELOG.

The glossary is not a substitute for the detailed contracts in the individual documents. It is a navigation aid and a consistency anchor. When in doubt, the detailed contract in the specific document governs.