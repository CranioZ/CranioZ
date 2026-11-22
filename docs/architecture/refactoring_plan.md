# CranioZ Refactoring Plan

**Document type:** Technical refactoring and execution plan
**Status:** Completed (2026-11-18)
**Parent plan:** implementation_plan.md
**Related handoff:** next_steps.md
**Related architectural review:** architectural_consolidation_plan.md
**Scope:** Structural reorganization of the Module and Editor packages, with associated dependency-boundary corrections
**Baseline (pre-refactoring):** 1633 passing tests, 0 failed, 0 errors, 2 skipped; ruff check, ruff format --check, and mypy src clean
**Baseline (post-refactoring):** 1635 passing tests, 0 failed, 0 errors, 2 skipped; ruff check, ruff format --check, and mypy src clean; 85% overall test coverage
**Last updated:** 2026-11-18

---

## 1. Purpose and Scope

This document defines the technical execution of the CranioZ package refactoring.

Its purpose is to reorganize the existing Module and Editor structures, establish explicit architectural boundaries, and prepare the codebase for the subsequent implementation of the Professional module and the expansion of clinical Editors.

The refactoring is aligned with **Phase 3 - Project, Home Page & Professional Module** of implementation_plan.md.

It is a supporting technical plan, not an independent implementation roadmap. It does not introduce new implementation phases, redefine existing sprints, or change the overall execution order established by the main plan.

**Classification note (per architectural_consolidation_plan.md section 2.1):** This work is a *Reorganization* under that document's taxonomy. It is executed now because it is a direct prerequisite of Sprint L (Professional module): implementing ProfessionalEditor under the current structure would create Workspace-Editor coupling that would immediately require a *Correction*. The justification is prevention of an imminent Correction, not structural preference.

**Parallelism note (per next_steps.md section 4):** This refactoring proceeds in parallel with Sprints I-K of Phase 3. Only Sprint L depends on its completion.

### 1.1 Objectives

1. Move Editor implementations out of ui/ and establish cranioz/editors/ as an independent package.
2. Separate Editor contracts from concrete Editor implementations.
3. Separate reusable Views and View-level overlays from concrete Editors.
4. Preserve the distinction between Editor functionality and Workspace presentation.
5. Separate Module contracts and infrastructure from built-in Module implementations.
6. Ensure Modules declare their UI requirements without depending on concrete Editor implementations or Workspace components.
7. Establish and enforce dependency boundaries through architecture tests.
8. Preserve existing functionality, lifecycle behavior, and public contracts during migration.
9. Prepare a stable architecture for the Professional module and subsequent Editor integration.
10. Consolidate the two duplicate PlaceholderEditor implementations identified in Step 1.

### 1.2 Scope

**Included:**

- modules/ package reorganization.
- ui/editors/ migration to cranioz/editors/.
- Editor and View contract separation.
- Reusable View and View Overlay organization.
- Workspace and Editor dependency-boundary corrections.
- Relevant application package naming cleanup.
- Test fixture migration (DummyEditor, DebugEditor, test-only Modules).
- Consolidation of the duplicate PlaceholderEditor implementations.
- Architecture tests and documentation updates.
- Relevant ADR updates.

**Not included:**

- Implementing the Professional module itself (Sprint L).
- Implementing ProjectIndex (Sprint I).
- Coordinated project deletion (Sprint J).
- Asynchronous Home Page loading (Sprint K).
- Implementing new clinical workflows or Editors.
- Implementing Phase 4 visualization features.
- Rewriting the Workspace engine or replacing EditorStack.
- Introducing new rendering engines or visualization dependencies.
- General performance optimization unrelated to the structural migration.
- Moving ThemeService, IconProvider, Toolbar, ToolRegistry, or ToolContext out of ui/. These remain approved presentation dependencies (see section 4).
- Fixing the implicit handler resolution in InMemoryModuleLoader (command_type._handler). Tracked in architectural_consolidation_plan.md section 4.4.
- Fixing the EditorStackSwitcher inline QSS (7 literals). Tracked in _KNOWN_DEBT_FILES.
- Fixing the missing icon_name declaration in the Editor ABC.

These items remain governed by implementation_plan.md and next_steps.md.

---

## 2. Architectural Decisions

### 2.1 Editor, Area, and EditorStack

The most important architectural distinction is the separation between functional Editors and Workspace composition.

**Editor**

An Editor is a functional work environment. It represents a domain-oriented user activity and is independent of its position within the Workspace.

Examples: tomography, cephalometry, osteotomy, patient, professional, console.

An Editor must not be identified by its current Workspace position.

**Area**

An Area is a presentation container belonging to the Workspace. It determines where content is displayed and how that content participates in the Workspace layout.

An Area may host one or multiple Editors.

**EditorStack**

An EditorStack manages the composition and switching of multiple Editors hosted by an Area.

It is a Workspace composition component, not an Editor implementation.

**Consequences:**

- Editor identity is functional, not positional.
- An Editor can be assigned to different Areas without changing its identity.
- Workspace layout determines the assignment of Editors to Areas.
- The same Editor implementation must not be duplicated merely because it is displayed in another Area.
- EditorStack and Area composition remain responsibilities of ui/workspace/.

**Valid Editor IDs** (examples): "tomography", "cephalometry", "osteotomy", "professional".

**Invalid functional Editor identities** (examples): "central.tomography", "left.professional", "right.console".

**Current state:** The codebase already uses functional IDs everywhere. EditorRegistry resolves by editor_id: str with no positional concept. EditorLayoutSpec LEAF nodes carry editor_id: str. ModuleUISpec references editor_id via EditorLayoutSpec. No positional Editor IDs exist. No serialized layout exists yet (layout_io.py is empty). No identifier migration is required.

### 2.2 Editor Package Boundaries

The Editor package is organized around four responsibilities:

1. Editor contracts and lifecycle.
2. View contracts and composition.
3. Reusable visualization implementations.
4. Concrete functional Editors.

These responsibilities must not be conflated.

**Editor core** defines what an Editor is and how it is registered, identified, configured, and managed.

**View core** defines the contracts and composition mechanisms for visualization Views.

**Views** provide reusable visualization implementations.

**Built-in Editors** assemble the necessary Views, controls, and application services into functional work environments.

### 2.3 Module Package Boundaries

Modules represent application capabilities and workflows.

They must remain declarative and independent of concrete Editor implementations.

A Module may declare UI requirements through stable contracts such as ModuleUISpec, referencing functional Editor IDs where necessary.

The application composition layer resolves those declarations against registered Editors and Workspace capabilities.

The Module system must not:

- Import concrete Editor implementations.
- Instantiate Workspace Areas.
- Create EditorStack instances.
- Depend on AreaWidget, Workspace, or application shell widgets.
- Define positional Editor identities.

This preserves the possibility of changing Workspace composition without rewriting clinical Modules.

---

## 3. Target Package Organization

The following structure represents the intended organization.

Only packages and files justified by existing responsibilities should be created. Do not introduce empty folders or speculative abstractions.

**Directory tree (text):**

    src/cranioz/
    |-- modules/
    |   |-- core/
    |   |   |-- errors.py
    |   |   |-- module.py
    |   |   |-- module_context.py
    |   |   |-- module_manifest.py
    |   |   |-- module_state.py
    |   |   |-- loader/
    |   |   |   `-- module_loader.py
    |   |   `-- registry/
    |   |       `-- module_registry.py
    |   `-- builtin/
    |       |-- alignment/
    |       |-- cephalometry/
    |       |-- orthognathic_guide/
    |       |-- osteotomies/
    |       |-- patient/
    |       |-- segmentation/
    |       `-- tomography/
    |
    |-- editors/
    |   |-- core/
    |   |   |-- editor/
    |   |   |   |-- base_editor.py
    |   |   |   |-- editor_catalog.py
    |   |   |   |-- editor_context.py
    |   |   |   |-- editor_manifest.py
    |   |   |   |-- editor_registry.py
    |   |   |   `-- placeholder_editor.py
    |   |   `-- view/
    |   |       |-- view.py
    |   |       |-- view_layout_renderer.py
    |   |       `-- view_layout_spec.py
    |   |
    |   |-- views/
    |   |   |-- mpr_viewer/
    |   |   `-- viewport_3d/
    |   |
    |   |-- view_overlays/
    |   |   |-- gizmos/
    |   |   `-- rulers/
    |   |
    |   `-- builtin/
    |       |-- tomography/
    |       `-- mesh_debug/
    |
    `-- ui/
        |-- home/
        |-- workspace/
        |-- toolbars/
        |-- tools/
        |-- theme/
        |-- icons/
        `-- widgets/

### 3.1 modules/core/

Contains the Module system contracts and infrastructure:

- Module base contract.
- Module context.
- Module manifest.
- Module state.
- Module errors.
- Module loader.
- Module registry.

The existing modules/base/ and other legacy organizational structures should be consolidated into this package where applicable.

No additional base/ or _internal/ layer should be introduced without a demonstrated need.

### 3.2 modules/builtin/

Contains concrete built-in Modules.

Each Module should retain its own manifest and implementation where applicable.

The package must not contain test-only Modules or depend on concrete Editor implementations.

cephalometry/ currently contains only __init__.py (no manifest.py, no module.py). It must not be loaded as a functional Module. The loader must ignore or report it according to the established loader contract. Decide in Step 1 whether it is a planned-but-incomplete Module or an obsolete directory.

### 3.3 editors/core/editor/

Contains the fundamental Editor contracts:

- Base Editor implementation.
- Editor context.
- Editor manifest.
- Editor registry.
- Editor catalog.
- Placeholder Editor.

These components define Editor identity, lifecycle, discovery, and registration.

They must remain independent of concrete Editor implementations and Workspace Areas.

**Open Decision:** editor_manifest.py and editor_catalog.py are currently empty. See section 7, decisions 1 and 2. Moving an empty file does not constitute migration.

### 3.4 editors/core/view/

Contains the View contracts and the mechanisms responsible for arranging Views within an Editor.

view_layout_renderer.py and view_layout_spec.py belong here: they are responsible for View-level composition. The ViewLayoutRenderer takes an optional editor: Editor parameter (used for the ACTIVE_ONLY policy and the activation event filter); this creates a real and necessary dependency editors.core.view -> editors.core.editor. See section 4.

Workspace-level composition (AreaLayoutRenderer, EditorStack, AreaLayoutSpec, EditorLayoutSpec, EditorStackOrientation) remains in ui/workspace/areas/.

### 3.5 editors/views/

Contains reusable visualization implementations.

Initial organization:

- mpr_viewer/
- viewport_3d/

panoramic/ is not present today. Do not create it speculatively; add it when a concrete panoramic View exists.

Views should be reusable by multiple Editors without importing concrete Editor implementations.

For the MPR implementation, slice_view.py should be created only if axial, coronal, and sagittal Views demonstrably share implementation logic, such as window/level handling, slice scrolling, or coordinate conversion.

Do not introduce an abstraction solely to reduce the number of files.

### 3.6 editors/view_overlays/

Contains reusable components attached to Views.

Examples:

- 3D gizmos.
- 2D rulers.
- Other View-level visual or interaction overlays.

These components must depend on the View contracts, not on concrete Editors.

### 3.7 editors/builtin/

Contains concrete functional Editor implementations.

Examples:

- TomographyEditor.
- MeshDebugEditor (see section 5.7 - decision required).
- Future: CephalometryEditor, OsteotomyEditor, PatientEditor, ProfessionalEditor, ConsoleEditor.

An Editor may compose multiple Views, overlays, toolbars, and application services.

The package must not be organized by Workspace position.

**Note on future Editors:** CephalometryEditor, OsteotomyEditor, PatientEditor, ProfessionalEditor, and ConsoleEditor are not implemented today. Do not create empty directories for them. Add them when Sprint L and subsequent clinical sprints deliver them.

### 3.8 ui/workspace/

Retains all Workspace composition responsibilities:

- Workspace.
- Areas and Area widgets.
- Area layout (AreaLayoutRenderer, AreaLayoutSpec).
- Editor layout (EditorLayoutSpec, EditorStackOrientation).
- EditorStack and EditorStackSwitcher.
- Workspace-level overlays.
- LayoutBuilder.
- Workspace specifications and composition (workspace_spec.py).

The EditorStack implementation delivered in Sprint H must not be moved to editors/.

The EditorLayoutSpec, EditorStackOrientation, and the specs/editor_layout_spec.py compatibility shim remain in ui/workspace/.

The Workspace resolves the relationship between functional Editor IDs and presentation Areas.

### 3.9 Shared UI and Appearance System

The ui/ package continues to own application presentation and shell components.

Preserve:

- Home Page.
- Workspace.
- Toolbars.
- Tools.
- Themes.
- Icons.
- Shared widgets.

The migration must preserve ADR-0014: Qt Widgets + modular QSS + Python Design Tokens.

It must also preserve ADR-0013, including the distinction between Editor layout, View layout, and toolbar placement.

---

## 4. Dependency Rules

The following dependency boundaries must be enforced through architecture tests.

**Approved dependencies (text):**

    domain
        -> imports nothing from higher CranioZ layers

    application
        -> domain

    infrastructure
        -> domain, application

    modules.core
        -> domain, application

    modules.builtin
        -> modules.core, domain, application

    editors.core.editor
        -> domain, application, infrastructure,
           ui.tools, ui.icons, ui.theme.service
           (approved presentation dependencies)

    editors.core.view
        -> domain, application, infrastructure,
           editors.core.editor,
           ui.toolbars, ui.theme.service, ui.icons, ui.tools,
           PySide6
           (approved presentation dependencies)

    editors.views
        -> editors.core.view, domain, application, infrastructure,
           ui.toolbars, ui.theme.service, ui.icons, ui.tools,
           PySide6, NumPy,
           approved external visualization dependencies

    editors.views.mpr_viewer
        -> editors.core.view, domain, application,
           ui.toolbars, PySide6, NumPy
           (no ui.theme dependency; MPRView uses QImage, not tokens)

    editors.view_overlays
        -> editors.core.view, domain, application,
           PySide6, VTK,
           approved external visualization dependencies

    editors.builtin
        -> editors.core.editor, editors.core.view,
           editors.views, editors.view_overlays,
           domain, application, infrastructure,
           ui.toolbars, ui.theme.service, ui.icons, ui.tools,
           PySide6, VTK, NumPy

    ui.workspace
        -> editors.core.editor, application,
           Workspace composition components

    ui
        -> application, infrastructure services,
           editors contracts and approved presentation dependencies

    cranioz.__main__, ui.main_window
        -> editors.builtin (composition root only)
           (explicit exception to section 4.1 rule 8)

### 4.1 Additional Restrictions

1. modules.core must not import editors.
2. modules.builtin must not import concrete Editors or Workspace components.
3. Modules may reference functional Editor IDs through declarative specifications.
4. editors.core.editor must not depend on concrete Editors, Modules, or Workspace Areas.
5. editors.core.view must not depend on concrete Editors.
6. editors.views and editors.view_overlays must not depend on each other.
7. editors.builtin may compose reusable Views and overlays but must not implement Workspace-level composition.
8. ui.workspace must not import concrete Editor implementations directly when the EditorRegistry or another approved composition contract can resolve them.
9. Workspace layout must not determine Editor identity.
10. No higher-level package may introduce dependencies into domain/.
11. editors.core.* must not import ui.theme.compiler. QSS global application is shell-only (the ThemeCompiler is the single owner of QApplication.setStyleSheet).
12. cranioz.__main__ and ui.main_window may import concrete Editors for registration. This is the approved composition mechanism. The restriction in rule 8 applies to ui.workspace, not to the composition root.
13. ui.workspace.find_viewport_3d() currently imports Viewport3DView lazily. This is a documented exception to rule 8. See section 7, decision 9.

External dependencies such as PySide6, VTK, NumPy, and other approved libraries must be explicitly accounted for in the relevant architecture tests.

### 4.2 Migration Note on ui.theme, ui.icons, ui.toolbars, ui.tools

The full migration of ThemeService, IconProvider, Toolbar, ToolRegistry, and ToolContext out of ui/ is **out of scope** for this refactoring. The rules above treat them as approved presentation dependencies of editors.core.*, editors.views, and editors.builtin. A future ADR may decide whether they move to a shared presentation/ package.

ThemeService (the token-reading API) is a permitted dependency; ThemeCompiler (the QSS-applying component) is not. editors.* may consume theme tokens through ThemeService, but must not apply a global stylesheet.

---

## 5. Execution Sequence

The execution sequence below describes the refactoring itself.

It does not replace or duplicate the functional deliverables of Phase 3.

### Step 0 - Pre-refactoring Cleanup (Separate Commit)

Before structural migration, remove debug instrumentation that the migration would otherwise carry into new locations.

**0.1. Remove debug print statements**

LayoutBuilder._instantiate_editors and AreaLayoutRenderer.render, _materialize_tree, _materialize_stack, _materialize_split contain print() calls with [DEBUG ...] prefixes. Replace with _logger.debug(...) where the information is useful; remove otherwise.

**0.2. Commit separately**

This is a hygiene commit, not a structural migration. It leaves the project in a valid, testable state.

### Step 1 - Pre-refactoring Inspection

Perform read-only inspection before moving files.

**1.1. Identify references and consumers**

Search for references to: mock, test_editor, mesh_debug, MeshDebug, objetos, posicao, central.tomography, left.professional, right.console, _PlaceholderEditor.

Inspect:

- module_loader.
- module_registry.
- editor_registry.
- editor_catalog.
- EditorManifest.
- ModuleUISpec.
- LayoutBuilder.
- layout_io.
- Workspace specifications.
- All relevant manifest.py files.
- Tests and fixtures.
- Debug scripts.

Identify imports, dynamically resolved names, serialized identifiers, and any string-based references.

**1.2. Verify the current Editor and Workspace contracts**

Confirm:

- Which classes own Editor identity.
- How Editors are registered and instantiated.
- How EditorContext is propagated.
- How ModuleUISpec declares Editor requirements.
- How Workspace composition resolves Editor IDs.
- How EditorStack receives and disposes Editor instances.
- Which components are responsible for View layout versus Workspace layout.

**Known findings from the 2026-11-16 inspection (already confirmed):**

- The registry, layout specs, workspace, and workspace specs use functional IDs everywhere. No positional IDs exist.
- layout_io.py is empty. No serialized layout exists. No identifier migration is required.
- ViewLayoutRenderer imports Editor at module level and takes editor: Editor | None in its constructor. The dependency editors.core.view -> editors.core.editor is real and tested.
- Editor (base_editor.py) imports ToolContext from ui.tools.registry.tool_definition at module level. editors.core.editor -> ui.tools is real.
- EditorContext imports IconProvider, ThemeService, ToolRegistry (TYPE_CHECKING) and TranslationService from infrastructure.i18n. editors.core.editor -> ui.icons, ui.theme.service, ui.tools, infrastructure.i18n are real.
- MPRView does not import ui.theme. It imports ui.toolbars (TYPE_CHECKING for ToolbarSpec) and ui.editors.view (which moves to editors.core.view).
- EditorStackOrientation is defined in ui/workspace/areas/editor_layout_spec.py and imported by editor_stack.py. Both stay in ui/workspace/areas/. No move.
- workspace_spec.py::_PlaceholderEditor is a byte-for-byte duplicate of ui/editors/placeholder_editor.py::PlaceholderEditor. Consolidation is an opportunity to reduce _KNOWN_DEBT_FILES from 8 to 7.
- ui/main_window.py imports MeshDebugEditor at module level (not lazily) for the CRANIOZ_DEBUG_MESH=1 path.
- ui/main_window.py and cranioz/__main__.py import and register TomographyEditor concretely (composition root).
- ui/editors/builtin/test_editor.py contains DummyEditor and DebugEditor. DummyEditor is used by 5 tests plus conftest.py. DebugEditor is used by scripts/debug_workspace.py.

**1.3. Resolve the following Open Decisions before migration (see section 7):**

- editor_manifest.py and editor_catalog.py are empty. Decide: implement, defer to Sprint L, or remove.
- MeshDebugEditor: keep (migrate to editors/builtin/mesh_debug/) or remove the CRANIOZ_DEBUG_MESH feature.
- Workspace.find_viewport_3d(): replace with a contract query or document as an exception.
- _PlaceholderEditor duplication: consolidate or document.

**Exit condition:** The actual dependency and consumer map is documented. No structural migration begins before the relevant ambiguities are resolved.

### Step 2 - Establish Architecture Tests

Create or update architecture tests before the structural migration.

The tests must enforce the dependency rules in section 4, including the approved presentation dependencies (ui.toolbars, ui.theme.service, ui.icons, ui.tools), the prohibition on ui.theme.compiler, and the composition-root exception for cranioz.__main__ and ui.main_window.

At minimum, verify:

- domain isolation.
- application dependency boundaries.
- Module isolation from concrete Editors and Workspace components.
- Editor core isolation from concrete Editors and Modules.
- View and View Overlay independence.
- Workspace dependence on Editor contracts rather than concrete Editor implementations.
- editors.core.* does not import ui.theme.compiler.
- No imports from obsolete package paths after migration.

Where practical, use explicit pytest architecture tests with AST inspection. The rule set is specific enough (many ad-hoc restrictions) that a declarative import-linter configuration may be less expressive. Fix the choice in Step 2.

The tests must be specific enough to prevent accidental coupling without blocking legitimate dependencies on approved external libraries.

**Exit condition:** The architectural rules are executable and their current violations are documented.

### Step 3 - Module System Reorganization

Create modules/core/ and move the existing Module contracts and infrastructure into it.

Move:

- Module contracts.
- Module context.
- Module manifest.
- Module state.
- Module errors.
- Module loader.
- Module registry.

Preserve public APIs through deliberate exports where needed.

Move built-in Modules into modules/builtin/ and ensure their manifests and implementation files remain correctly discoverable.

Remove the duplicate _null_task_manager.py implementation and reuse the canonical NoopTaskManager from application/tasks/.

The loader must handle incomplete or intentionally absent Modules correctly.

For example, a directory such as cephalometry/ without a valid manifest.py and module.py must not be loaded as a functional Module. It should be ignored or reported according to the established loader contract.

**Test impact:** tests/unit/modules/test_module_loader.py imports from cranioz.modules.base.*, cranioz.modules.errors, cranioz.modules.loader.module_loader, and cranioz.modules.registry.module_registry. Update all imports in the same commit. Do not fix the implicit handler resolution (command_type._handler) in the same commit; it is tracked in architectural_consolidation_plan.md section 4.4.

**Exit condition:**

- Module discovery and registration work.
- Built-in Modules remain discoverable.
- Test-only Modules are not part of production discovery.
- Modules do not import concrete Editors or Workspace components.
- All relevant tests pass.

### Step 4 - Editor Package Reorganization

Create the top-level cranioz/editors/ package.

Use git mv whenever possible to preserve file history.

**4.1. Move Editor contracts**

Move the Editor contract and registry components into editors/core/editor/.

This includes the existing base Editor (base_editor.py), context (editor_context.py), registry (editor_registry.py), and placeholder implementation (placeholder_editor.py).

editor_manifest.py and editor_catalog.py are currently empty. See section 7, decisions 1 and 2, before moving them.

**Test impact:** tests/unit/ui/editors/test_editor_registry.py, tests/unit/ui/editors/test_editor_context.py, tests/unit/ui/editors/test_editor_active_view.py, tests/integration/ui/workspace/test_editor_context_propagation.py, tests/unit/ui/workspace/areas/test_editor_stack.py, tests/integration/ui/workspace/test_workspace.py, tests/integration/ui/workspace/layout/test_layout_builder.py, tests/integration/ui/workspace/test_layout_renderer.py, tests/integration/ui/workspace/areas/test_area_layout_renderer.py, tests/integration/ui/workspace/areas/test_area_widget.py, and tests/conftest.py all import from cranioz.ui.editors.*. Update all imports in the same commit.

test_editor_active_view.py also references logger="cranioz.ui.editors.base_editor" in two caplog.at_level calls. Update those to the new logger name.

**4.2. Move View contracts**

Move View-level contracts and layout components into editors/core/view/.

Only components responsible for View-level composition belong here.

Move view.py, view_layout_renderer.py, view_layout_spec.py.

**Test impact:** tests/unit/ui/editors/test_view_layout_renderer_active_only.py, tests/unit/ui/editors/test_view.py (if it exists), tests/unit/ui/editors/test_view_layout_spec.py (if it exists), and tests/integration/ui/editors/test_tomography_editor_active_view.py import from cranioz.ui.editors.view*. Update imports in the same commit.

**4.3. Move reusable Views**

Move:

- MPR Viewer (ui/editors/mpr_viewer/).
- 3D Viewport (ui/editors/viewport_3d/).

Into editors/views/.

Preserve their rendering behavior and lifecycle.

viewport_3d/presets.py is tracked in _KNOWN_DEBT_FILES with 3 literals. Update the path in _KNOWN_DEBT_FILES and _DEBT_MAX_LITERALS in the same commit.

**Test impact:** tests/integration/ui/editors/test_tomography_editor_active_view.py imports MPRView from cranioz.ui.editors.mpr_viewer.view and patches "cranioz.ui.editors.tomography.editor.Viewport3DView". Update both the import and the patch target string in the same commit.

**4.4. Move reusable View overlays**

Move existing gizmos and rulers into editors/view_overlays/.

Preserve their current functionality and public contracts.

**4.5. Move concrete Editors**

Move functional Editor implementations into editors/builtin/.

Organize by functional responsibility, not by Area.

For example: editors/builtin/tomography/editor.py.

Do not create editors/areas/central/tomography/ or editors/areas/left/professional/.

**MeshDebugEditor decision required (see section 7, decision 15):** ui/main_window.py imports MeshDebugEditor at module level. If kept, move it to editors/builtin/mesh_debug/editor.py and update main_window.py's import. If removed, delete the CRANIOZ_DEBUG_MESH path from main_window.py and workspace_spec.py (DEBUG_MESH) in a separate commit first.

**Test impact:** tests/integration/ui/editors/test_tomography_editor_active_view.py imports TomographyEditor from cranioz.ui.editors.tomography.editor. tests/conftest.py imports it too. Update both imports.

**4.6. Preserve Workspace composition**

Keep the following in ui/workspace/:

- Area.
- AreaWidget.
- AreaLayoutRenderer.
- AreaLayoutSpec.
- EditorLayoutSpec.
- EditorStack.
- EditorStackSwitcher.
- EditorStackOrientation (defined in editor_layout_spec.py).
- LayoutBuilder.
- Workspace layout specifications.
- Workspace overlays.
- workspace_spec.py and the specs/editor_layout_spec.py shim.

The Workspace must continue to resolve functional Editor IDs through the approved registration and composition mechanisms.

**4.7. Correct Editor identity**

The codebase already uses functional Editor IDs. No positional IDs exist. No migration is required.

Document this in the ADR (Step 7). Do not add a migration mechanism for identifiers that do not exist.

**Exit condition:**

- All concrete Editors are available through the new package.
- Editor registration works.
- Workspace composition remains functional.
- EditorStack behavior is preserved.
- No positional Editor identity exists in the functional Editor registry.
- No production imports depend on the obsolete ui/editors/ paths.

### Step 5 - Remove Obsolete Components and Test-Only Production Code

Remove components that are confirmed to be obsolete or duplicated.

**5.1. Remove debug-only mock Editors**

Remove ui/editors/mock/ (all four files: console.py, mpr.py, objetos.py, posicao.py).

Remove their entries from _KNOWN_DEBT_FILES and _DEBT_MAX_LITERALS (ui/editors/mock/mpr.py: 10, ui/editors/mock/objetos.py: 8) in the same commit.

Do not remove Mock* debug Editors merely because their names contain mock. Confirm no consumers exist before removal.

**5.2. Move DummyEditor and DebugEditor to test fixtures**

ui/editors/builtin/test_editor.py contains DummyEditor and DebugEditor.

DummyEditor is used by:

- tests/unit/ui/editors/test_editor_registry.py.
- tests/integration/ui/workspace/test_workspace.py.
- tests/integration/ui/workspace/layout/test_layout_builder.py.
- tests/integration/ui/workspace/test_layout_renderer.py.
- tests/integration/ui/workspace/areas/test_area_layout_renderer.py.
- tests/integration/ui/workspace/areas/test_area_widget.py.
- tests/integration/ui/workspace/test_editor_context_propagation.py.
- tests/conftest.py.

DebugEditor is used by scripts/debug_workspace.py.

**Action:**

- Move DummyEditor to tests/fixtures/editors/dummy_editor.py.
- Move DebugEditor to tests/fixtures/editors/debug_editor.py (or keep both in the same file if the tests permit it).
- Update all imports in the same commit.
- Update scripts/debug_workspace.py's import.
- Remove ui/editors/builtin/test_editor.py.

Do not remove the file while consumers exist.

**5.3. Move test-only Modules**

Move modules/builtin/test_modules/ to tests/fixtures/test_modules/.

Update test discovery and any fixtures that consume these Modules.

**5.4. Consolidate PlaceholderEditor implementations**

ui/editors/placeholder_editor.py and ui/workspace/workspace_spec.py::_PlaceholderEditor are byte-for-byte equivalent (same editor_id, title, content_widget(), QSS, initialize, _tr).

**Action:**

- Make workspace_spec.py import PlaceholderEditor and PLACEHOLDER_EDITOR_ID from editors/core/editor/placeholder_editor.py.
- Remove the private _PlaceholderEditor class.
- Remove ui/workspace/workspace_spec.py from _KNOWN_DEBT_FILES (1 literal removed).
- Reduce _DEBT_MAX_LITERALS total by 1.

This reduces _KNOWN_DEBT_FILES from 8 to 7 and removes duplication.

**If not consolidated:** document why the two must differ. There is no evidence they do.

**5.5. Update _KNOWN_DEBT_FILES**

The following files move or are removed. Update _KNOWN_DEBT_FILES and _DEBT_MAX_LITERALS in the same commit as the file migration or removal.

| File | Action | Budget |
|---|---|---|
| ui/editors/viewport_3d/presets.py | Move to editors/views/viewport_3d/presets.py | 3 (unchanged) |
| ui/editors/placeholder_editor.py | Move to editors/core/editor/placeholder_editor.py | 1 (unchanged) |
| ui/editors/mock/mpr.py | Remove (Step 5.1) | Remove entry |
| ui/editors/mock/objetos.py | Remove (Step 5.1) | Remove entry |
| ui/workspace/workspace_spec.py | Keep path; remove _PlaceholderEditor (Step 5.4) | Remove entry if consolidated |
| ui/workspace/areas/area_widget.py | Does not move | 5 (unchanged) |
| ui/workspace/workspace.py | Does not move | 3 (unchanged) |
| ui/workspace/areas/editor_stack.py | Does not move | 7 (unchanged) |

test_debt_max_matches_debt_files enforces that _KNOWN_DEBT_FILES and _DEBT_MAX_LITERALS are updated together.

**5.6. Update logger names in tests**

tests/unit/ui/editors/test_editor_active_view.py references logger="cranioz.ui.editors.base_editor" in two caplog.at_level calls. Update to "cranioz.editors.core.editor.base_editor" in the same commit that moves base_editor.py.

**5.7. Update patch target strings**

tests/integration/ui/editors/test_tomography_editor_active_view.py uses patch("cranioz.ui.editors.tomography.editor.Viewport3DView", _FakeViewport3DView). After migration, the target becomes "cranioz.editors.builtin.tomography.editor.Viewport3DView". Update in the same commit.

**5.8. Update shim imports in tests**

tests/integration/ui/workspace/test_workspace.py, tests/integration/ui/workspace/layout/test_layout_builder.py, tests/integration/ui/workspace/test_layout_renderer.py, and tests/integration/ui/workspace/areas/test_area_layout_renderer.py import EditorLayoutSpec from cranioz.ui.workspace.specs.editor_layout_spec (the compatibility shim). Update them to import from cranioz.ui.workspace.areas.editor_layout_spec (the canonical implementation) in the same commit that confirms EditorLayoutSpec stays in ui/workspace/areas/. The shim should have no test consumers after the migration.

tests/unit/ui/workspace/areas/test_editor_stack.py imports EditorStackOrientation from cranioz.ui.workspace.areas.editor_stack, but the canonical definition is in editor_layout_spec.py. Update the import to cranioz.ui.workspace.areas.editor_layout_spec.

**5.9. Update workspace_spec.py re-exports**

ui/workspace/workspace_spec.py re-exports PLACEHOLDER_EDITOR_CLASS and PLACEHOLDER_EDITOR_ID. When placeholder_editor.py moves to editors/core/editor/, update the re-export in workspace_spec.py. conftest.py and main_window.py import from workspace_spec.py, so they do not need to change.

**5.10. event_bus.py migration is independent**

The application/event_bus.py -> application/events/bus.py migration (Step 6.1) is independent of the Editor refactoring. tests/integration/ui/workspace/test_editor_context_propagation.py imports EventBus from the old path. If Step 6.1 is executed in the same PR as the Editor migration, the test needs a double import update. Prefer separate PRs to keep scopes clean.

**Exit condition:** No obsolete production components, duplicated implementations, or test-only production Modules remain unintentionally. _KNOWN_DEBT_FILES and _DEBT_MAX_LITERALS reflect the post-migration state.

### Step 6 - Application Package Naming Cleanup

Perform the following changes only after confirming their current contracts and consumers.

**6.1. Event Bus**

application/event_bus.py -> application/events/bus.py.

Update imports and tests. Prefer a separate PR from the Editor migration.

**6.2. Project package naming**

Remove redundant project_ prefixes from files inside application/project/ where appropriate.

Examples:

    project_manager.py              -> manager.py
    project_catalog.py              -> catalog.py
    project_context.py              -> context.py
    project_errors.py               -> errors.py
    project_events.py               -> events.py
    project_access_policy.py        -> access_policy.py
    project_repository.py           -> repository.py
    in_memory_project_repository.py -> in_memory_repository.py

Preserve the package's public API and update imports.

**6.3. Preferences**

Move settings/preferences.py to application/settings/preferences.py only if inspection confirms that the module provides a high-level application API without direct Qt or filesystem dependencies.

Otherwise, retain or move it to the appropriate infrastructure package.

**Exit condition:** Naming is consistent, imports are updated, and application contracts remain unchanged.

### Step 7 - ADR and Architecture Documentation

Update ADR-0013 or create a short ADR documenting the structural decisions.

The documentation must record:

1. Editors are a top-level package, independent of ui/.
2. Editor identity is functional and position-independent.
3. Area is a Workspace presentation container.
4. EditorStack belongs to Workspace composition.
5. Editor core and View core have separate responsibilities.
6. Reusable Views and View overlays are independent packages.
7. Modules remain declarative and do not depend on concrete Editors.
8. Workspace composition resolves functional Editor IDs.
9. The dependency rules in section 4 are authoritative.
10. editors.core.* may consume ThemeService but not ThemeCompiler.
11. cranioz.__main__ and ui.main_window are the approved composition root; the section 4.1 rule 8 restriction applies to ui.workspace, not to them.
12. No positional Editor IDs exist and no migration is required.
13. ThemeService, IconProvider, Toolbar, ToolRegistry, and ToolContext remain in ui/ as approved presentation dependencies. Moving them to a shared presentation/ package is a candidate for a future ADR.
14. The two PlaceholderEditor implementations have been consolidated (or the reason they remain separate is documented).

Update relevant package documentation and architectural diagrams.

Do not duplicate the entire technical execution plan in the ADR.

**Exit condition:** The architectural decisions are documented, consistent with the implementation, and referenced by the relevant package documentation.

### Step 8 - Final Validation

Run the complete validation suite.

Required commands (PowerShell):

    .venv\Scripts\python.exe -m pytest
    .venv\Scripts\python.exe -m ruff check .
    .venv\Scripts\python.exe -m ruff format --check .
    .venv\Scripts\python.exe -m mypy src

Validate the following integration scenarios:

- Module discovery.
- Editor registration.
- Editor creation and disposal.
- EditorStack switching.
- Workspace Area composition.
- View rendering.
- ModuleUISpec resolution.
- Debug Workspace rendering.
- Existing Home Page and project workflows.
- PlaceholderEditor consolidation (if Step 5.4 was executed).

Additionally:

- Verify that no obsolete import paths remain.
- Verify that architecture tests enforce the intended boundaries.
- Verify that editors.core.* does not import ui.theme.compiler.
- Verify that cranioz.__main__ and ui.main_window are allowed to import concrete Editors (composition root).
- Confirm that no regression has been introduced in appearance-token enforcement.
- Confirm that _KNOWN_DEBT_FILES and _DEBT_MAX_LITERALS match the post-migration file set.

**Exit condition:** All validation commands pass, relevant integration scenarios work, and the architectural boundaries are enforced.

---

## 6. Commit Strategy

Each logical migration must be committed independently.

Use git mv whenever possible to preserve history.

Recommended commit sequence:

| Commit | Scope |
|---|---|
| 0 | Pre-refactoring cleanup (debug print removal) |
| 1 | Architecture boundary tests |
| 2 | Module core and built-in Module reorganization |
| 3 | Editor core contracts migration |
| 4 | View contracts and reusable Views migration |
| 5 | View overlays migration |
| 6 | Concrete Editor migration |
| 7 | Workspace and Editor registration integration |
| 8 | Test fixture migration (DummyEditor, DebugEditor, test-only Modules) |
| 9 | Obsolete components cleanup (ui/editors/mock/, _KNOWN_DEBT_FILES update) |
| 10 | PlaceholderEditor consolidation (if approved in Step 1.3) |
| 11 | Application package naming cleanup (prefer separate PR) |
| 12 | ADR and architecture documentation |

The sequence may be adjusted if inspection reveals a necessary dependency between migrations.

Each commit must leave the project in a valid, testable state.

**Required validation after each commit:**

- Relevant unit and integration tests.
- ruff check .
- ruff format --check .
- mypy src

Run the complete test suite at the end of each major migration boundary and before declaring the refactoring complete.

Do not combine unrelated functional changes with structural migration commits.

---

## 7. Open Decisions

The following decisions must be resolved during Step 1, before their corresponding migrations.

| # | Decision | Required verification / action |
|---|---|---|
| 1 | editor_manifest.py empty | Decide: (a) implement as part of this refactoring, (b) defer to Sprint L, (c) remove. Moving an empty file is not migration. |
| 2 | editor_catalog.py empty | Same as #1. The EditorRegistry docstring delegates filtering-by-context to the EditorCatalog; the contract is referenced but not implemented. |
| 3 | ViewLayoutRenderer -> Editor | Accept. The dependency is real, necessary for ACTIVE_ONLY, and tested. Document in section 4. |
| 4 | editors.core.* -> infrastructure | Accept. ThemeService -> settings, EditorContext -> infrastructure.i18n. Document in section 4. |
| 5 | ThemeService vs ThemeCompiler | Distinguish: ThemeService (token-reading API) permitted; ThemeCompiler (QSS-applying component) prohibited in editors.*. Document in section 4.1. |
| 6 | PySide6 explicit | Include in section 4 approved dependency list for editors.core.view, editors.views, editors.view_overlays, editors.builtin. |
| 7 | MPRView -> ui.theme | Resolved: MPRView does not import ui.theme. No action. |
| 8 | Move ui/theme out of ui/ | Out of scope. Document in section 1.2 and section 4.2. |
| 9 | Workspace.find_viewport_3d() | Decide: (a) replace with an Editor.find_view(type) contract query, or (b) document as a permitted exception to section 4.1 rule 8. Add a regression test either way; no test exists today. |
| 10 | Debug print in LayoutBuilder / AreaLayoutRenderer | Remove in Step 0. Replace with _logger.debug(...) where useful. |
| 11 | EditorStackSwitcher QSS inline | Tracked in _KNOWN_DEBT_FILES. The Editor refactoring does not move editor_stack.py, so the debt is not paid. Document in section 8. |
| 12 | DummyEditor in test_editor.py | Move to tests/fixtures/editors/dummy_editor.py. Update 8 imports. See Step 5.2. |
| 13 | Shim EditorLayoutSpec imports | Update 4 tests to import from areas/. See Step 5.8. |
| 14 | event_bus.py migration | Prefer a separate PR. See Step 5.10. |
| 15 | MeshDebugEditor imported by MainWindow | Decide: (a) migrate to editors/builtin/mesh_debug/ and update the import, or (b) remove the CRANIOZ_DEBUG_MESH feature in a separate commit. Do not remove the file in Step 5 without addressing main_window.py. |
| 16 | TomographyEditor in composition root | Explicitly permitted. Document as an exception to section 4.1 rule 8. |
| 17 | EditorStackOrientation canonical location | Resolved: defined in ui/workspace/areas/editor_layout_spec.py, re-imported by editor_stack.py. Nothing moves. Update test_editor_stack.py import as hygiene. |
| 18 | workspace_spec.py re-exports PlaceholderEditor | Update the re-export when placeholder_editor.py moves (Step 5.9). If Step 5.4 consolidates the two placeholders, the re-export becomes an import of the canonical PlaceholderEditor. |
| 19 | Duplicate PlaceholderEditor implementations | Byte-for-byte duplicate. Consolidate in Step 5.4. Reduces _KNOWN_DEBT_FILES from 8 to 7. If not consolidated, document why. |
| 20 | DebugEditor in test_editor.py | Move to tests/fixtures/editors/ alongside DummyEditor. Update scripts/debug_workspace.py's import. See Step 5.2. |

No decision should be made solely to match the proposed directory tree.

---

## 8. Risks and Safeguards

| Risk | Safeguard |
|---|---|
| Circular imports after package migration | Architecture tests and explicit dependency boundaries |
| Broken dynamic imports | Pre-refactoring reference inspection and integration tests |
| Broken saved layouts | Not applicable: layout_io.py is empty; no positional Editor IDs exist; no serialized layout exists. |
| Workspace regression | Preserve Area and EditorStack contracts; test composition independently |
| Module coupling to Editors | Keep ModuleUISpec declarative and resolve through the composition layer |
| Duplicate implementations | Verify canonical implementations before removal. PlaceholderEditor is the only duplicate identified; consolidate in Step 5.4. |
| Loss of Git history | Use git mv |
| Appearance regression | Update _KNOWN_DEBT_FILES in the same commit and run architecture tests. EditorStackSwitcher QSS inline is tracked and not paid by this refactoring. |
| Unnecessary abstractions | Introduce only contracts justified by actual shared responsibilities |
| Scope expansion | Keep functional Sprint I-L deliverables outside this document |
| MeshDebugEditor removal breaks MainWindow | Decide in Step 1.3 before Step 5. |
| DummyEditor removal breaks 8 consumers | Move to tests/fixtures/editors/ first (Step 5.2). |
| Editor.icon_name missing from ABC | EditorStackSwitcher uses getattr(editor, "icon_name", None). Not a refactoring blocker; register as debt. |
| Implicit handler resolution in InMemoryModuleLoader | Not fixed by this refactoring. Tracked in architectural_consolidation_plan.md section 4.4. Update imports only when module_loader.py moves. |
| theme_service / IconProvider migration out of ui/ | Out of scope. Documented in section 1.2 and section 4.2. |

---

## 9. Completion Criteria

The refactoring is complete when:

- [x] Debug print statements removed from LayoutBuilder and AreaLayoutRenderer (Step 0).
- [x] modules/core/ and modules/builtin/ are correctly separated.
- [x] cranioz/editors/ exists as the canonical Editor package.
- [x] Editor contracts and View contracts have distinct responsibilities.
- [x] Reusable Views are separated from concrete Editors.
- [x] View overlays are separated from concrete Editors.
- [x] Concrete Editors are organized by functional responsibility.
- [x] Editor identity is independent of Workspace position.
- [x] Area, AreaLayoutRenderer, EditorLayoutSpec, EditorStack, EditorStackOrientation, and EditorStackSwitcher remain in ui/workspace/areas/.
- [x] Modules remain declarative and independent of concrete Editors.
- [x] Workspace resolves functional Editor IDs through approved contracts.
- [x] cranioz.__main__ and ui.main_window are documented as the composition root exception.
- [x] Test-only Modules and debug-only production components are handled correctly.
- [x] DummyEditor and DebugEditor moved to tests/fixtures/editors/.
- [x] PlaceholderEditor duplicate consolidated (or divergence documented).
- [x] Obsolete and duplicated components are removed after verification.
- [x] _KNOWN_DEBT_FILES and _DEBT_MAX_LITERALS reflect the post-migration file set.
- [x] Relevant application naming cleanup is complete or explicitly deferred.
- [x] Architecture tests enforce the intended dependency boundaries.
- [x] ADR and package documentation reflect the final architecture.
- [x] Existing functional behavior and lifecycle contracts are preserved.
- [x] pytest, ruff check, ruff format --check, and mypy src pass.
- [x] All changes are committed independently and the final state is validated.

---

## 10. Relationship with the Other CranioZ Planning Documents

This document is subordinate to the main implementation roadmap.

### implementation_plan.md

Defines the overall implementation phases, functional deliverables, and completion criteria.

This refactoring supports Phase 3 and prepares the architecture for the Professional module and subsequent Editor integration.

It does not redefine Phase 3 or create additional implementation phases.

### next_steps.md

Defines the immediate work sequence and the current development handoff.

The Editor Architecture Refactoring is one of the next work items identified after Sprint H. Sprint I (ProjectIndex) remains a separate Phase 3 deliverable.

This document provides the detailed technical procedure for executing the refactoring.

The refactoring proceeds in parallel with Sprints I-K. Only Sprint L depends on its completion.

### architectural_consolidation_plan.md

Records architectural inconsistencies, duplication, legacy components, and consolidation requirements.

The refactoring may resolve items identified there (e.g., the PlaceholderEditor duplicate), but it must not automatically absorb unrelated consolidation tasks.

Any additional issue discovered during execution should be recorded in the appropriate planning document rather than silently expanding this scope.

### Document authority

When a conflict exists:

1. implementation_plan.md governs the overall implementation roadmap.
2. next_steps.md governs immediate execution priorities and handoff.
3. architectural_consolidation_plan.md governs architectural consolidation findings.
4. refactoring_plan.md governs the technical execution of the structural refactoring within its approved scope.

The four documents must remain consistent, but each must preserve its own purpose.

---

## 11. Post-Refactoring Notes

The refactoring was completed on 2026-11-18.

**Deviations from the original plan:**

- **Step 6.1** (`main_window` → `main_window`) was explicitly deferred to a separate PR, per the recommendation in §5.10. It is independent of the structural refactoring.
- **Step 4.4** (`editors/view_overlays/`) was skipped because `editors` and `editors` contained only empty `__init__.py` files. No content was migrated; the package will be created when a concrete overlay implementation exists.

**Resolved open decisions (§7):**

- **#1 / #2:** `editor_manifest.py` and `editor_catalog.py` were removed. If a contract is needed for Sprint L, it will be introduced with a real implementation.
- **#9:** `Workspace.find_viewport_3d()` was kept as a documented exception to §4.1 rule 8. A regression test is tracked as follow-up.
- **#15:** `MeshDebugEditor` was kept and migrated to `editors/builtin/mesh_debug/editor.py`.
- **#19:** The `_PlaceholderEditor` duplicate was consolidated into the canonical `PlaceholderEditor`. `_KNOWN_DEBT_FILES` was reduced from 8 to 5 files.

**Final validation:**

- `pytest`: 1635 passed, 0 failed, 0 errors, 2 skipped.
- `ruff check`: clean.
- `ruff format --check`: clean.
- `mypy src`: clean (281 files).
- `coverage report`: 85% overall.

**Architectural outcome:**

See ADR-0015 (`docs/adr/ADR-0015_Editor_and_Module_Package_Reorganization.md`) for the recorded architecture.

**Next work item:**

Sprint I (ProjectIndex), per `next_steps.md` §5.1.