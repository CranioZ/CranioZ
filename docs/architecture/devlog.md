# Dev Log

Narrative record of CranioZ's engineering and design decisions.
Each entry covers a work session or a sprint. `git log` records the
*what*; this file records the *why*, what was tried and discarded, and
what was left pending.

The log starts at Sprint E. Everything before it is summarized below
and detailed in `git log` and `implementation_plan.md`.


29c990d | 2026-11-09 22:39:45 -0300 | Jozeias Fernandes de Sousa | Refactor(ui): G2 ÔÇö Toolbar per View (ViewLayoutRenderer)
- ADR-0013 ┬º2.6: add ToolbarVisibilityMode.ACTIVE_ONLY
- View: add toolbar_specs()/control_panel_specs() (default empty)
- ViewLayoutRenderer: wrap each View with its Toolbars; cache
  containers by view_id; sizePolicy Expanding + min 200x150 so the
  QSplitter distributes available space
- AreaLayoutRenderer: stop materializing Toolbars
- AreaWidget: stop creating Toolbars; drop tool_registry/
  theme_service/icon_provider usage (kept on signature for
  LayoutRenderer compatibility, removed in Sprint H)
- MPRView/Viewport3DView: declare View-level Toolbars with
  ACTIVE_ONLY
- Viewport3DView: min size 200x150 on container
- TomographyEditor: build the ViewLayoutRenderer from the
  EditorContext deps; capture renderer in a local for mypy
- conftest.py: harden VTK finalize with shiboken6.isValid
  (prevents STATUS_HEAP_CORRUPTION on Windows teardown)
- Tests: update 8 files; add test_view_layout_renderer_toolbars.py
  (7 tests: materialization, positions, cache, clear_cache,
  View/Area separation)

Test baseline: 1528 -> 1539 passed.
Visual validation: scripts/debug/ui/workspace/debug_workspace.py
shows the 2x2 grid with four View-level Toolbar pairs and the
3D View rendering the synthetic volume.
Known polishment (Sprint H / widget migration): grid container
sizePolicy, Toolbar button width (Toggle cuts to 'Toggl'),
Toolbar alignment (center vs top), toggle icon missing from
catalog.

229c869 | 2026-11-09 22:24:19 -0300 | Jozeias Fernandes de Sousa | Refactor(ui): G2 ÔÇö Toolbar per View (ViewLayoutRenderer)
- ADR-0013 ┬º2.6: add ToolbarVisibilityMode.ACTIVE_ONLY
- View: add toolbar_specs()/control_panel_specs() (default empty)
- ViewLayoutRenderer: wrap each View with its Toolbars; cache
  containers by view_id; clear on clear_cache()
- AreaLayoutRenderer: stop materializing Toolbars
- AreaWidget: stop creating Toolbars; drop tool_registry/
  theme_service/icon_provider usage (kept on signature for
  LayoutRenderer compatibility, removed in Sprint H)
- MPRView/Viewport3DView: declare View-level Toolbars with
  ACTIVE_ONLY
- TomographyEditor: build the ViewLayoutRenderer from the
  EditorContext deps; capture renderer in a local for mypy
- conftest.py: harden VTK finalize with shiboken6.isValid
  (prevents STATUS_HEAP_CORRUPTION on Windows teardown)
- Tests: update 8 files; add test_view_layout_renderer_toolbars.py
  (7 tests: materialization, positions, cache, clear_cache,
  View/Area separation)

Test baseline: 1528 ÔåÆ 1539 passed.

77000de | 2026-11-09 20:38:12 -0300 | Jozeias Fernandes de Sousa | Docs

12cafb8 | 2026-11-09 20:24:50 -0300 | Jozeias Fernandes de Sousa | Context: complete Sprint C ÔÇö EditorContext propagation
Propagate theme_service and icon_provider through EditorContext, and
add the contract test that asserts every Editor receives the full set
of nine fields. This closes the remaining Phase 1 blocker.

Production:
- EditorContext: add theme_service and icon_provider fields (optional,
  default None, consistent with the other context fields)
- Workspace.load_spec: pass theme_service and icon_provider in the
  shared_context handed to LayoutBuilder

Tests:
- tests/integration/ui/workspace/test_editor_context_propagation.py:
  contract test that builds a real Workspace, loads a ModuleUISpec,
  and asserts the expected instance for each propagated field

Not asserted here (tracked as debt, see Next Steps.md ┬º7):
- correlation_id: not yet propagated by Workspace
- event_subscription: passed as None; a dedicated test should cover it
  once the EventBus exposes a subscription helper for unit tests
- domain_object_store: not in the Sprint C target set

Baseline:
- Before: 1527 passing
- After:  1528 passing, 0 failed, 0 errors, 0 skipped
- ruff, ruff format, mypy: clean

fdcadaa | 2026-11-09 15:33:00 -0300 | Jozeias Fernandes de Sousa | feat(icons): complete Sprint F ÔÇö IconProvider + UnicodeIconProvider + glyph migration
Deliver the icon system for Phase 2 and unblock Sprint C (EditorContext
propagation). Implements the closed 60-icon catalog behind the IconProvider
Protocol, injects the provider into every shell widget that renders a glyph,
migrates the hardcoded glyphs to provider.icon(...), and adds the five icon
contract tests.

Production:
- IconState enum (DEFAULT, HOVER, PRESSED, SELECTED, DISABLED)
- IconProvider Protocol (icon, text_glyph, invalidate_cache)
- UnicodeIconProvider with the closed 60-icon catalog
- Injection into MainWindow, Workspace, HomePage, HomeSegment,
  ModulesSegment, ExtrasSegment, Toolbar, StartButton, FlowRow
- Hardcoded glyphs migrated to provider.icon(...)
- _WHITELIST emptied (Sprint B glyph debt paid)

Tests:
- 5 icon contract test files (catalog, fallback, theme, widget contract,
  accessibility)
- make_icon_provider factory and icon_provider fixture in conftest.py
- 17 test files updated to pass icon_provider to constructors
- test_toolbar_resolves_icon_name_via_theme renamed to
  test_toolbar_resolves_icon_via_icon_provider, now asserting
  button.icon().isNull() is False
- test_unknown_tool_id_raises rewritten with pytest.raises (ruff F841)

Docs:
- implementation_plan.md: Sprint F closed, Phase 2 pending work reduced,
  baseline updated to 1527 passing
- Next Steps.md: Sprint F complete, next sprint changed to Sprint C,
  baseline updated

Baseline:
- Before: 1508 passing, 1 skipped
- After:  1527 passing, 0 failed, 0 errors, 0 skipped, 88% coverage
- ruff, ruff format, mypy: clean

Known deprecations tracked separately:
- QImage.mirrored (mpr_viewer/view.py:216)
- vtkCellArray.GetData (stl.py:135)

fb0933e | 2026-11-09 13:50:42 -0300 | Jozeias Fernandes de Sousa | style(appearance): modern dark palette, expanded QSS, and StartButton/FlowRow migration
- tokens.py: DARK palette migrated to modern-dark neutral greys with
  iOS-inspired system colors. feedback_information kept at #4A90D9
  (spec value) to pass WCAG AA on background.panel.
- compiler.py: _build_qss expanded to cover QTableWidget + QHeaderView,
  QScrollBar, QLineEdit placeholder and focus, QComboBox dropdown,
  QLabel roles (title/subtitle/caption/arrow), QFrame cards, QMenu,
  QToolTip, StartButton states, and FlowRow checked/step/separator/arrow.
- start_button.py: removed inline setStyleSheet. Now uses
  property("state", "enabled"|"disabled") and the global QSS. Sprint F
  will swap the glyph for IconProvider.icon(...).
- flow_row.py: removed inline setStyleSheet. Now uses
  property("checked", "true"|"false"), objectName for step/separator,
  and class="arrow" for arrows.
- test_no_hardcoded_appearance.py: _KNOWN_DEBT_FILES reduced from 10 to
  4 files (the 6 icon-target files have zero hardcoded literals). The
  budget is now exact (==), not an upper bound (<=).
- test_compiler.py: _FakeQApplication is a QApplication subclass, so
  the monkeypatch no longer needs a false # type: ignore.

1508 passed, 0 failed, 1 skipped. Coverage unchanged.

docs(devlog): start the engineering log

a3b392c | 2026-11-08 23:40:26 -0300 | Jozeias Fernandes de Sousa | docs(plan): mark Sprint E complete and point next steps to Sprint F
- implementation_plan.md
  - Phase 2: ThemeService, ThemeCompiler, tokens, and the settings
    package are marked as delivered.
  - Sprint table: E moves from Pending to Complete.
  - Definition of Done: item 12 scoped to _KNOWN_DEBT_FILES so the
    frozen widget-migration debt is explicit.
  - Known issues: add ┬º10.13 (Sprint E deliverables, 177 tests added,
    known debt frozen in 6 files / 26 literals).
  - Implementation summary: reflect 1510 passing, 0 failed, 88% coverage.

- Next Steps.md
  - Scope updated to "after Sprint E closure".
  - ┬º2.2: test count and Sprint E delivery recorded.
  - ┬º3.2: Sprint E marked Complete; Sprint F/G/H remain Pending.
  - ┬º4: sprint table updated; next sprint is F.
  - ┬º7: known issues table updated (Sprint E complete, hardcoded
    colors guarded, widget migration tracked as debt).
  - ┬º8: immediate next action is Sprint F (IconProvider +
    UnicodeIconProvider + glyph migration), with acceptance criteria.

No code changes. CI remains green (ruff, mypy, 1510 tests passing,
1 skipped, 88% coverage).

fbb2260 | 2026-11-08 23:33:51 -0300 | Jozeias Fernandes de Sousa | Appearance: implement design tokens, ThemeService, and ThemeCompiler (Sprint E)
Introduce the canonical appearance foundation described in
docs/architecture/appearance/themes-and-design-tokens.md.

Infrastructure
--------------
- Add cranioz.infrastructure.settings package:
  - SettingsService protocol
  - InMemorySettingsService and FilesystemSettingsService
  - SettingsStore with typed get(), closed KNOWN_KEYS, atomic save()
  - SettingsMigrator (schema v1)
  - SettingsError, SettingsMigrationError
- AppPathResolver gains settings_root and user_settings_path()
- PathsConfig gains settings_root (defaults to ~/.cranioz/Settings)
- paths.json gains settings_root: null

Theme
-----
- tokens.py: ThemeMode, ThemeName (StrEnum), 8 token dataclasses,
  47 canonical tokens for DARK and LIGHT, validate_tokens/validate_all_themes
- service.py: ThemeService rewritten
  - mode/set_mode/theme/tokens/color/dimension/surface_color/icon_name
  - SYSTEM resolution via QStyleHints.colorScheme(), DARK fallback
  - theme_changed signal, reactivity to colorSchemeChanged
  - persistence read through SettingsService; set_mode does not persist
- compiler.py: ThemeCompiler + CompiledStyles
  - surface composition (toolbar, popover, modal_backdrop)
  - modal_backdrop base is a fixed #000000 per spec ┬º6.2
  - QSS emission for the standard Qt controls
  - apply() is the single owner of QApplication.setStyleSheet
- __main__.py: boot order now
  SettingsService -> ThemeService -> apply theme -> MainWindow

Tests
-----
- +177 passing (1509 total, 0 failed, 1 skipped)
- unit/ui/theme: test_service, test_tokens, test_compiler
- unit/infrastructure/settings: test_settings_service
- architecture: no_hardcoded_appearance, tokens_used, tokens_present,
  theme_completeness, theme_values, contrast (WCAG 2.2 AA)
- existing UI/integration tests migrated to the new ThemeService signature
- test_app_path_resolver updated for settings_root

Known debt
----------
- _KNOWN_DEBT_FILES in test_no_hardcoded_appearance.py freezes the
  pre-existing hardcoded colors in:
    home/widgets/flow_row.py            (9)
    home/widgets/start_button.py        (5)
    workspace/areas/area_widget.py      (5)
    workspace/workspace.py              (3)
    workspace/workspace_spec.py         (1)
    editors/viewport_3d/presets.py      (3)
  These are the migration target for the widget migration sprint.

0824092 | 2026-11-08 01:00:37 -0300 | Jozeias Fernandes de Sousa | Update: implementation_plan.md and next_steps.md.

aaf3077 | 2026-11-08 00:54:25 -0300 | Jozeias Fernandes de Sousa | i18n(B.3.2): add placeholder and dialog keys to workspace catalogs i18n(B.3.2): add startup error keys to core catalogs i18n(B.3.2): migrate MainWindow to tr() i18n(B.3.2): migrate HomePage widgets to tr() i18n(B.3.2): migrate Top Bar segments to tr() i18n(B.3.2): translate Workspace placeholder editor i18n(B.3.2): translate bootstrap startup error test(B.3.2): add real ModulesSegment tests test(B.3.3): guard against hardcoded strings in shell widgets

725d643 | 2026-11-08 00:02:57 -0300 | Jozeias Fernandes de Sousa | i18n(B.3.1): add flows.json catalogs, fixtures and contract test

92b7540 | 2026-11-07 23:24:04 -0300 | Jozeias Fernandes de Sousa | i18n(B.2): propagate translation_service through EditorContext, Workspace, MainWindow and HomePage
- EditorContext gains translation_service (Sprint C field).
- LayoutBuilder propagates translation_service via shared_context.
- Workspace receives and forwards translation_service.
- MainWindow receives translation_service and injects it into HomePage and Workspace.
- HomePage accepts translation_service and translates flows via self._translation.tr(...).
- TomographyEditor translates toolbar titles via EditorContext.translation_service.
- __main__.py builds CatalogTranslationService and injects it into MainWindow.
- _humanize_translation_key removed.
- Contract tests added for EditorContext and LayoutBuilder.
- ruff, mypy and pytest green (1317 passed).

6519208 | 2026-11-07 22:47:54 -0300 | Jozeias Fernandes de Sousa | i18n: add translation catalogs for en and pt-BR
- Add core, homepage, workspace, patient, professional,
  tomography, cephalometry, osteotomy, import_dialog,
  and bottom_panels catalogs in en/ and pt-BR/.
- Populate with keys extracted from the current shell widgets
  and the Prototipagem_UI_17 specification.
- Standardize the locale directory name to pt-BR (BCP 47).

c289c87 | 2026-11-07 11:41:37 -0300 | Jozeias Fernandes de Sousa | docs(architecture): establish appearance architecture and close Phase 1ÔÇô3 blockers
Establish the canonical appearance architecture for CranioZ and align the
implementation plan and next steps with the architectural decisions made
in this round.

Appearance architecture (docs/architecture/appearance/):
- README.md: scope and index
- appearance-architecture.md: layered architecture
  (configuration -> design tokens -> style system -> Qt Widgets
  -> medical visualization color system)
- themes-and-design-tokens.md: seven token categories, 47 tokens,
  ThemeMode (DARK, LIGHT, SYSTEM) and ThemeName, ThemeService,
  ThemeCompiler with four explicit responsibilities, surface
  composition, translucency rules, WCAG AA contrast tests, and
  the boundary between shared and intrinsic properties
- icons.md: IconProvider Protocol, UnicodeIconProvider (Phase 2),
  SvgIconProvider (Phase 8), 60-icon catalog, state rendering,
  accessibility, fallback behavior, widget migration roadmap
- surfaces-and-overlays.md: Solid, Translucent, Simulated Glass;
  real background blur is not supported by design

ADR:
- ADR-0014 (Widget Toolkit Selection) registers the decision to adopt
  Qt Widgets with a modular QSS design system driven by semantic
  design tokens. QML was evaluated and rejected as the shell
  foundation due to the cost of bridging multiple
  QVTKRenderWindowInteractor instances; isolated future migration of
  the HomePage remains possible. The ADR references the architecture
  documents instead of duplicating them, and supersedes the legacy
  ADR-0003 (widget library and semantic colors).

Implementation plan and next steps:
- Phases 1, 2, and 3 are marked In Progress with detailed sprints:
  - Sprint B: i18n contract, catalogs, widget injection
  - Sprint C: EditorContext propagation (task_manager, telemetry,
    correlation_id, command_dispatcher, scene_query,
    event_subscription, translation_service, theme_service,
    icon_provider)
  - Sprint E: ThemeService, ThemeCompiler, 47 tokens, contract tests
  - Sprint F: IconProvider, UnicodeIconProvider, glyph migration
  - Sprint G: AreaLayoutRenderer
  - Sprint H: EditorStack
  - Sprint I: ProjectIndex (interface, InMemory, Filesystem)
  - Sprint J: Coordinated project deletion
  - Sprint K: Async project and flow loading
  - Sprint L: Professional module
- Phase 4 remains the next major implementation phase and begins only
  after Phases 1ÔÇô3 are marked Implemented.
- The steps_panel overlay is removed from the roadmap and replaced by
  WorkflowBreadcrumb in the Top Bar (Phase 5).
- Real background blur is documented as unsupported by design.
- The DICOM visualization bug is documented as resolved
  (voxel ordering, int16, direction matrix).

No production code is changed by this commit. The appearance
architecture is a specification; its implementation happens in
Sprints E and F.

Refs: ADR-0014, docs/architecture/appearance/, implementation_plan.md,
next_steps.md

de71ed4 | 2026-11-07 00:26:31 -0300 | Jozeias Fernandes de Sousa | Imaging: correct DICOM voxel ordering and stabilize 3D view
- VtkImageAdapter: remove transpose(2,1,0) + ravel("C") combination
  that corrupted the memory layout of vtkImageData. The correct
  conversion is data.ravel(order="C") on the native (Z, Y, X)
  layout with SetDimensions(nx, ny, nz).
- VtkImageAdapter: switch to VTK_SHORT (int16) as the production
  scalar type. Benchmarks on the reference dataset showed 17x
  faster conversion and 81% higher FPS than uint8, with full
  HU fidelity preserved.
- VtkImageAdapter: apply SetDirectionMatrix from Volume.geometry
  so the volume respects the anatomical RAS orientation.
- Viewport3DView: replace QTimer.singleShot with a persistent
  QTimer owned by the view; dispose() stops the timer before
  destroying the interactor. Fixes "Internal C++ object already
  deleted" and "wglMakeCurrent failed" in integration tests.
- Viewport3DView: fix silent bug in camera height calculation
  (bounds[3] - bounds[3] was always zero).
- MainWindow: register built-in tools (tool.log, tool.toggle)
  before creating the Workspace, so the default editor spec can
  resolve its toolbars.
- MPRView: annotate slice_changed as SignalInstance (mypy).
- Tests: add regression tests for voxel ordering, int16 fidelity
  and negative value preservation; add spacing_z test using
  ImagePositionPatient distance.

Closes: dicom-visualization-bug

e63aeee | 2026-11-06 14:48:41 -0300 | Jozeias Fernandes de Sousa | MPR: render axial, coronal, sagittal via VTK with Compatibility Profile
- __main__.py: force QSurfaceFormat Compatibility Profile (OpenGL 2.1)
  and AA_ShareOpenGLContexts before creating QApplication. PySide6 6.5+
  defaults to Core Profile 3.2, which VTK 9 does not support on Windows
  with QVTKRenderWindowInteractor.
- MPRView: reset DirectionMatrix to identity on the vtkImageData used
  by vtkImageSliceMapper. The VtkImageAdapter applies LPS->RAS direction
  (diag(-1, -1, 1)) so the 3D volume renders correctly; the slice mapper
  must ignore that matrix to compute correct slice bounds. Without the
  reset, the axial view produced horizontal banding and an empty frame.
- workspace_spec: the default ModuleUISpec now hosts TomographyEditor
  in the Central Area instead of the placeholder. Import of a DICOM
  series now shows the four Views (axial, coronal, sagittal, 3D).

The 3D volume rendering (vtkSmartVolumeMapper) still needs work; it is
handled in a follow-up commit.

cebfa73 | 2026-11-05 20:15:13 -0300 | Jozeias Fernandes de Sousa | feat(dc): reestrutura UI com abas + extra├º├úo + persist├¬ncia
- MainWindow com docks (├írvore, hist├│rico, console) + QTabWidget central
- Aba Qualidade: Ruff, Pytest, Coverage, Run All com streaming
- Aba Extra├º├úo: 3 modos (C├│digo, Docs, ├ürvore) com extens├Áes condicionais
- ConfigManager: persist├¬ncia por aba em ~/.cranioz/dc_config.json
- Workers separados em ui/workers.py para evitar import circular
- Bot├úo Clear History no dock de hist├│rico
- ├ürvore de pastas colapsada com raiz expandida

7fdd79a | 2026-11-05 09:29:40 -0300 | Jozeias Fernandes de Sousa | Debug: add MeshDebugEditor and STL validation pipeline

1530f07 | 2026-11-04 23:46:32 -0300 | Jozeias Fernandes de Sousa | feat(debug): add MeshDebugEditor and STL validation pipeline

57e0795 | 2026-11-04 23:17:59 -0300 | Jozeias Fernandes de Sousa | Development_center: Restructures UI with tabs and integrates code extraction
- Reorganizes MainWindow using docks (tree, history, output) and a central QTabWidget
- Adds tabs: Quality, Extraction, Documentation (placeholder), Build (placeholder), and Architecture (placeholder)
- Implements a unified Extraction tab with 3 modes: Code, Documentation, and Folder Tree
- Adds conditional selection of file extensions based on the selected mode
- Moves Workers to `ui/workers.py` to avoid circular imports
- Adds a "Clear History" button to the history dock
- Sets the folder tree to start in a collapsed state, with only the root node expanded

8657e12 | 2026-11-02 23:47:25 -0300 | Jozeias Fernandes de Sousa | ui): render STL meshes in Viewport3DView for pipeline validation
Add a second rendering path to the Viewport3DView, independent of the
DICOM volume path (adapter, reslice, transfer functions). The new
set_mesh() method receives a canonical Mesh (from the Geometry
Infrastructure domain), converts it to vtkPolyData via the existing
mesh_to_polydata adapter, and renders it as a vtkActor. The volume
and the mesh can coexist in the same renderer.

Wire the feature into the application via the Top Bar's HomeSegment:

- The 'Importar arquivos' menu item becomes a submenu with two
  entries: 'DICOM (s├®rie)' (current production path) and 'STL (debug)'
  (temporary validation tool, marked TODO(phase-4)).
- MainWindow._on_import_stl_debug_clicked opens a file dialog, reads
  the STL via read_stl (explicit unit_scale=1.0 and RAS frame), and
  writes the Mesh into the first Viewport3DView found by
  Workspace.find_viewport_3d().
- Workspace.find_viewport_3d walks Areas -> Editors -> Views and
  returns the first Viewport3DView, or None. The Viewport3DView
  type is imported under TYPE_CHECKING for the annotation, and
  imported locally for the isinstance check (to avoid a runtime
  import cycle).

The set_mesh path does not depend on the DICOM visualization bug
(┬º10.5). If an STL renders correctly, the renderer, camera and
OpenGL context are healthy; any remaining volume-rendering issue
lives in the vtkImageData path.

Phase 4, Section 4.4 (Geometry Infrastructure, initial subset)

a633eba | 2026-11-02 23:28:41 -0300 | Jozeias Fernandes de Sousa | geometry): add STL I/O and Mesh -> vtkPolyData adapter
Implement the initial I/O and VTK adapter subset of the Geometry
Infrastructure document (Phase 2, STL portion):

- read_stl: parse an STL file into a canonical Mesh, with explicit
  unit_scale and coordinate_frame. The reader never assumes
  millimetres or RAS (┬º4.5 of the Geometry Infrastructure document).
- write_stl: export a Mesh as STL. No unit conversion is applied;
  the caller scales the vertices before export.
- mesh_to_polydata: convert a canonical Mesh into a vtkPolyData.
  The vertex buffer is shared (deep=0) when dtype and contiguity
  allow; the faces are converted to a vtkIdTypeArray for
  ImportLegacyFormat.

The reader does not weld vertices: two vertices with identical
coordinates remain distinct in the resulting Mesh.

The VTK 9.6+ deprecation of vtkCellArray.GetData() is acknowledged
and tracked; migrating to ExportLegacyFormat / GetConnectivityArray
is a separate piece for when VTK 10 removes GetData().

Phase 4, Section 4.4 (Geometry Infrastructure).

ecb06da | 2026-11-02 23:16:50 -0300 | Jozeias Fernandes de Sousa | Geometry: add canonical Mesh and CoordinateFrame
Introduce the initial subset of the Geometry Infrastructure domain:

- CoordinateFrame: the local frame a mesh declares (RAS by default).
- Mesh: immutable triangular mesh with shape/dtype/finiteness/index
  invariants and read-only arrays.
- ValidationIssue / ValidationResult / ValidationSeverity: the
  structured validation vocabulary (the profile registry is deferred).

No VTK, no I/O, no persistence. The initial subset validates the
geometry contracts before the STL import and VTK adapter land in
the next block.

Phase 4, Section 4.4 (Geometry Infrastructure).

c6aed50 | 2026-11-02 21:53:48 -0300 | Jozeias Fernandes de Sousa | Docs(plan): close Phase 2 Top Bar debt, track remaining Phase 2 items
Reflect the four commits that closed the Workspace Top Bar integration:

- TopOverlay now exposes set_left/center/right_content().
- HomeSegment, ModulesSegment, ExtrasSegment are implemented.
- Area toggles (Left, Right, Bottom) are wired to
  Workspace.set_area_visible().
- WorkspaceLayoutState (runtime visibility only) and
  LayoutRenderer.refresh_splitter_sizes() are in place.
- WorkspaceSpec.DEFAULT declares all four Areas; lateral Areas start
  hidden (prototype); Area.visible is the runtime source of truth
  for the Region computation.

┬º10.10 is marked resolved with the commit list. The remaining Phase 2
items are tracked in the new ┬º10.11: configurable Editor Layout Tree
(ADR-0013 ┬º7.3), Editor Stack (ADR-0013 ┬º2.5), IconManager, and
ThemeManager (ADR-0003, still Proposed).

Also corrects two stale entries: ┬º5.1 item 1 no longer asks to
'implement CommandExecutor' (┬º10.3 already marks it done), and ┬º4.3
'Memory and interoperability' no longer carries a typo line split.

Phase 2, Section 10.10.

e8423d3 | 2026-11-02 21:47:12 -0300 | Jozeias Fernandes de Sousa | ui): wire Top Bar toggles and hide lateral Areas by default
The default WorkspaceSpec now declares all four Areas (Left, Central,
Right, Bottom), each hosting the placeholder Editor. Left, Right and
Bottom start hidden (the prototype shows only the Central Area on
first load); the Top Bar toggles bring them on.

- WorkspaceSpec.DEFAULT: add Left, Right and Bottom AreaSpecs. The
  Central Area no longer uses 'editor.tomography' (the DICOM bug is
  still paused); all four Areas use the placeholder Editor.
- Workspace: add _hide_lateral_areas_by_default(), which hides the
  lateral Areas after each load_spec(), updates the WorkspaceLayoutState
  to match, and recomputes the splitter sizes so the Central Area
  takes the full surface. set_area_visible() now calls
  LayoutRenderer.refresh_splitter_sizes() after toggling, so the
  QSplitter actually reflows.
- LayoutRenderer: add refresh_splitter_sizes() to redistribute the
  QSplitter sizes after a child is hidden/shown. Filter
  compute_region_bounds by Area.visible (the runtime source of
  truth) instead of widget.isHidden() (which can lag inside a
  QSplitter). Use a loop instead of a double widget(i) call to
  satisfy mypy.
- AreaWidget: expose area() so the LayoutRenderer can read the
  model's visibility state.
- Tests: cover the toggle flow for Left, Bottom and Right, the
  splitter reflow, and the Region bounds exclusion. Adjust
  test_open_project_loads_default_spec for the new four-Area spec.

Phase 2, Section 10.10

02f18cf | 2026-11-02 21:30:18 -0300 | Jozeias Fernandes de Sousa | ui): exclude hidden Areas from Region bounds via Area.visible
The TopOverlay was being positioned over a Region that included an
Area the user had hidden. The root cause was a mismatch between the
model (Area.visible, set by set_area_visible) and the Qt widget
visibility (isHidden), which can lag behind inside a QSplitter.

- LayoutRenderer.compute_region_bounds: filter by Area.visible
  (the runtime source of truth) instead of widget.isHidden().
  The AreaWidget exposes the model via a new area() getter.
- Workspace: remove _hide_empty_lateral_areas. The concept of an
  'empty Area' does not exist at this level: every Area declared
  in a ModuleUISpec hosts at least one Editor (the placeholder or a
  real one). Areas without Editors are a spec decision, not a
  Workspace decision.
- Workspace._regions_from_bounds: keep the Area.visible filter,
  for consistency with compute_region_bounds.
- test_main_window_top_bar: replace the three duplicated
  test_empty_lateral_areas_are_hidden definitions with a single
  test_hidden_area_is_excluded_from_region_bounds, and move the
  imports to the top level.

Phase 2, Section 10.10.

61fecb3 | 2026-11-02 20:57:50 -0300 | Jozeias Fernandes de Sousa | UI: wire Top Bar segments and area toggles into Workspace
Integrate the three Top Bar segments into MainWindow._create_workspace()
and add the runtime visibility state that the Home/Extras toggles need.

- Workspace: add WorkspaceLayoutState (left/right/bottom visibility) and
  set_area_visible(placement, visible), which updates the model and the
  AreaWidget and repositions the overlays.
- MainWindow: inject HomeSegment, ModulesSegment and ExtrasSegment into
  the TopOverlay; wire each segment signal to its handler; add
  _toggle_area() to relay Home/Extras toggles to the Workspace.
- ModulesSegment is populated with a placeholder ('Tomografia') until
  Phase 5 delivers WorkflowEngine.
- conftest: add main_window_with_open_project fixture for integration
  tests that need a Workspace whose Top Bar is fully populated.
- Rewrite the six MainWindow tests that depended on the removed
  workspace.home_button QPushButton; they now locate the HomeSegment
  and emit close_workspace_requested, which is the architectural
  equivalent of the old 'Home' click.

Phase 2, Section 10.10.

6657334 | 2026-11-02 20:40:57 -0300 | Jozeias Fernandes de Sousa | add HomeSegment, ModulesSegment, ExtrasSegment for TopOverlay
Three presentation widgets for the Workspace Top Bar zones. Each
segment is a plain QWidget: it knows no Overlay, Region or Placement.

- HomeSegment: toggle Area Left, project menu (Novo/Abrir/Fechar/
  Importar), close workspace. 'Fechar projeto' and 'Importar arquivos'
  are enabled only while a project is open, reflected by
  set_project_open(bool).
- ModulesSegment: set_modules() populates module buttons (placeholder:
  'Tomografia' until Phase 5 delivers WorkflowEngine), set_selected()
  reflects the active module.
- ExtrasSegment: application-level menu (Configuracoes, Temas, Ajuda,
  Atualizacoes, Sobre) and the two Area toggles.

Icons are textual glyphs. A future piece will replace them with
ThemeService.icon_name() when the icon loader exists (ADR-0003).

Phase 2, Section 10.10.

48e24d5 | 2026-11-02 20:26:40 -0300 | Jozeias Fernandes de Sousa | add set_center_content / set_right_content to TopOverlay
Symmetric to set_left_content. The TopOverlay now exposes the full
three-segment injection API that the MainWindow will use to populate
the Home, Modules and Extras zones of the Top Bar (Phase 2, ┬º10.10).

The behavior is unchanged: each setter replaces the segment's content
via _replace_content, which is already used by set_left_content. The
tests cover injection, replacement and clearing for center and right,
plus a symmetry assertion across all three.

3c0202f | 2026-11-02 20:05:48 -0300 | Jozeias Fernandes de Sousa | test(ui): align preset tests with HU-aware Viewport3D selection
The Viewport3DView now picks its initial preset from the Volume's
IntensityScale: HU-calibrated volumes start at 'bone', non-HU
volumes start at 'cbct'. The DicomCalibrator is already covered by
five green unit tests, so the preset branch is the presentation
layer reacting to a contract that is known to work.

Changes:
- test_viewport_3d_view: add _make_volume()/_make_hu_volume(),
  expect 'cbct' for UNKNOWN volumes, cover the 'bone' branch.
- test_tomography_editor_mpr: expect 'cbct' for UNKNOWN volumes,
  add integration coverage for the HU branch.
- test_volume_presets: include 'cbct' in the expected PRESETS set
  and in the known-presets parametrization.
- conftest: apply AA_ShareOpenGLContexts and QSurfaceFormat before
  the QApplication is created; finalize live VTK interactors after
  each test to release their OpenGL context before Qt teardown;
  keep the conftest importable when VTK is absent.

The remaining VTK wglMakeCurrent warnings come from Qt deleting
interactors whose contexts VTK has already torn down. They do not
affect test outcomes and are logged at DEBUG by the teardown
fixture. A follow-up piece will address the lifetime on the
production side (explicit dispose() at every QVTKRenderWindow
Interactor creation site).

Result: 1236 passed, ruff clean, mypy clean.

794e41a | 2026-11-02 19:35:42 -0300 | Jozeias Fernandes de Sousa | docs: document DICOM visualization bug and pause correction
- Add `docs/known_issues/dicom_visualization_bug.md` with symptom,
  context, diagnosis, attempts, hypotheses, and next steps.
- Update `docs/architecture/implementation.md` to record the paused
  bug in Phase 4 (Visualization) and reference the known-issues
  document.
- Update the `Last updated` field.

The correction work is paused to avoid further trial-and-error. A
systematic approach is planned for when the work resumes.

6aaff77 | 2026-11-02 19:30:09 -0300 | Jozeias Fernandes de Sousa | docs(known-issues): document DICOM visualization bug and pause correction
- Add `docs/known_issues/dicom_visualization_bug.md` to record the
  open issue with DICOM visualization in the TomographyEditor.
- Document the symptom, context, diagnosis, and all correction
  attempts made so far.
- List hypotheses for the next iteration, including:
  - Verifying the actual direction matrix.
  - Investigating the MPR reslice axes and 3D transfer function.
  - Comparing with the legacy DicomEngine approach.
  - Testing with a synthetic volume.
- Pause the correction work to avoid further trial-and-error and
  resume with a systematic approach later.

Files changed:
- `docs/known_issues/dicom_visualization_bug.md` (new)

Related:
- `src/cranioz/infrastructure/visualization/vtk_image_adapter.py`
- `src/cranioz/ui/editors/mpr_viewer/view.py`
- `src/cranioz/ui/editors/viewport_3d/view.py`
- `src/cranioz/ui/editors/viewport_3d/presets.py`
- `src/cranioz/infrastructure/imaging/dicom/dicom_series_reader.py`

408e314 | 2026-11-02 12:46:20 -0300 | Jozeias Fernandes de Sousa | Docs(implementation): reflect Sprint 4.2 + 4.3 completion
- Remove the 'Sprint 4.2 (in progress)' block from ┬º5.1.
- Update ┬º4.3 to reflect Volume/VolumeGeometry/DicomSeriesReader/
  VtkImageAdapter as implemented, and VolumeData/dicom_loader as
  removed.
- Update ┬º4.3 'Memory and interoperability' to reflect the explicit
  buffer-ownership contract (┬º8.1).
- Refine ┬º4.4 Pending (W/L, orientation, lifecycle).
- Update ┬º10.4 Known Debt: mark resolved items, keep the remaining
  ones (storage modes, VTI export, import UI, patient identity).
- Update ┬º10.3: CommandExecutor/CommandDispatcher is implemented.

Refs: Sprint 4.2 + 4.3; Medical Imaging Infrastructure; Application
Startup ┬º3.1, ┬º3.4, ┬º4.1

d8a1a9e | 2026-11-02 12:41:50 -0300 | Jozeias Fernandes de Sousa | Imaging: consolidate Volume as the sole imaging aggregate
Sprint 4.2 + 4.3 ÔÇö Medical Imaging Infrastructure.

Views and Editor consume Volume (domain), not VolumeData or
vtkImageData:

- MPRView.set_volume(volume: Volume) converts via VtkImageAdapter and
  retains a strong reference to the Volume (shared NumPy buffer, ┬º8.1).
- Viewport3DView.set_volume(volume: Volume) does the same.
- TomographyEditor resolves the first Volume from the DomainObjectStore
  via SceneQuery and passes it to all four Views.
- The VtkImageAdapter is the sole bridge between Volume and
  vtkImageData (Medical Imaging Infrastructure ┬º3.2).

MainWindow uses the Command architecture for DICOM import:

- _on_import_dicom_clicked dispatches ImportDicomSeriesCommand through
  the CommandDispatcher instead of the legacy loader.
- The ImportDicomSeriesHandler is registered in the CommandBus when a
  project is opened (_on_project_open_requested) and unregistered when
  the project closes (_on_home_clicked). The handler is imported
  locally, so pydicom/numpy stay out of the boot critical path
  (Application Startup ┬º3.1, ┬º3.4, ┬º4.1; Medical Imaging
  Infrastructure ┬º3.3).

Removed the legacy VolumeData and loader:

- Deleted domain/scene/volume_data.py.
- Deleted infrastructure/imaging/dicom_loader.py.
- Deleted tests/unit/infrastructure/imaging/test_dicom_loader.py.
- Moved _write_synthetic_dcm into the integration test that still
  needs it.
- Updated the docstring of test_import_dicom.py (VolumeData -> Volume).

Updated implementation.md (Sprint 4.2 / 4.3 status).

Refs: ADR-0007, ADR-0008, ADR-0013; Medical Imaging Infrastructure
┬º3.2, ┬º3.3, ┬º7, ┬º8.1, ┬º11.7; Application Startup ┬º3.1, ┬º3.4, ┬º4.1

c391663 | 2026-11-02 11:54:17 -0300 | Jozeias Fernandes de Sousa | Docs(implementation): correct visualization status and register Sprint 4.2
MPRView uses a manual vtkImageReslice pipeline, not vtkResliceImageViewer.
Viewport3DView already renders volumes via vtkSmartVolumeMapper with presets.
The vtkOutlineFilter is a complementary visual aid, not a placeholder.

Register Sprint 4.2 (Consume Volume in Views and Editors) as in progress.

Refs: ┬º4.4, ┬º5.1, ┬º10.5

209f693 | 2026-11-02 11:41:01 -0300 | Jozeias Fernandes de Sousa | Imaging: consolidate DICOM import and Volume -> VTK bridge
Sprint 4.1 ÔÇö Medical Imaging Infrastructure.

Add VtkImageAdapter (Volume -> vtkImageData), preserving origin,
spacing, direction matrix, and scalar data without copying the
NumPy buffer.

Refactor ImportDicomSeriesHandler to use DicomSeriesReader, which
assembles a domain Volume from a DICOM series (validation, physical
slice ordering, LPS->RAS conversion, intensity calibration, provenance).

Update ImportDicomSeriesCommand docstring: path is a folder, not a file.

Fix SetDirectionMatrix call: vtkImageData.SetDirectionMatrix (VTK 9+)
accepts 9 floats (3x3 row-major), not a vtkMatrix4x4.

Fix GetDirectionMatrix test: it returns a vtkMatrix3x3, not a list;
use GetElement(row, col) to read values.

Extend _write_synthetic_dcm to include ImageOrientationPatient,
PixelSpacing, and RescaleSlope/Intercept. DicomSorter requires
ImageOrientationPatient to compute the direction matrix.

Update integration test to read series_uid from
Volume.metadata.series_instance_uid (the Volume aggregate does not
carry series_uid directly).

Remove test_to_vtk_rejects_unsupported_dtype: Volume.__post_init__
already rejects unsupported dtypes, so the adapter cannot receive one.

Refs: Medical Imaging Infrastructure ┬º5.2, ┬º5.3, ┬º8.1, ┬º12.1;
ADR-0007, ADR-0008"

f17beb5 | 2026-11-02 11:08:59 -0300 | Jozeias Fernandes de Sousa | Test(imaging): add unit tests for DICOM infrastructure
- Add tests for DicomSorter (sorting, direction, gantry tilt)
- Add tests for DicomCalibrator (HU vs UNCALIBRATED)
- Add tests for DicomValidator (dimensions, spacing, transfer syntax)
- Add tests for DicomSeriesReader (end-to-end with synthetic DICOMs
  including ImageOrientationPatient)
- Add tests for ImportReport (severity, summary)
- Fix ruff RUF012, PLC0415, E402, RUF059, F401

Refs: Medical Imaging Infrastructure ┬º5, ┬º7, Implementation Plan Phase 4 ┬º4.3

8271e53 | 2026-11-02 10:53:07 -0300 | Jozeias Fernandes de Sousa | Imaging: add DICOM infrastructure (Sprint 3 structure)
- Add ImportReport and ImportIssue (Application layer)
- Add DicomSorter (slice ordering + direction matrix)
- Add DicomCalibrator (RescaleSlope/Intercept + IntensityScale)
- Add DicomValidator (geometry, transfer syntax, spacing)
- Add DicomSeriesReader (orchestrator, produces Volume)
- Fix ruff PLR1714, SIM103, RUF005, C401, B905, PLC0415, F401, F811
- Fix mypy direction tuple type

Refs: Medical Imaging Infrastructure ┬º5, ┬º7, Implementation Plan Phase 4 ┬º4.3

f653166 | 2026-11-02 10:31:49 -0300 | Jozeias Fernandes de Sousa | Domain: add medical imaging domain models
- Add Volume aggregate root with IntensityScale classification
- Add VolumeGeometry with direction matrix (orthonormality validated)
- Add index-to-world and world-to-index mapping
- Add ImageMetadata and ImageModality for DICOM-derived metadata
- Add VolumeProvenance for traceability
- Add CoordinateSystem enum (RAS, LPS, IJK)
- Add unit tests for geometry, volume, and sampling

Refs: Medical Imaging Infrastructure ┬º4.1-4.6, Implementation Plan Phase 4 ┬º4.3

140470a | 2026-11-02 00:12:16 -0300 | Jozeias Fernandes de Sousa | (commands): implement transactional CommandExecutor
- Add transaction boundary around Command dispatch (ADR-0007 ┬º2.3)
- Publish events only after successful commit (ADR-0007 ┬º2.4)
- Push reversible Commands to CommandStack for undo/redo
- Dispatch compensating Commands on undo through the same transaction
- Add contract tests covering dispatch, rollback, undo/redo, event publication
- Fix MPRView tests to match vtkImageReslice-based implementation
- Fix ruff and mypy issues in __main__.py, dicom_loader.py, executor.py

Refs: ADR-0007, Implementation Plan Phase 4 ┬º5.1 item 1

658b884 | 2026-11-01 23:56:55 -0300 | Jozeias Fernandes de Sousa | Update of implementation.md

98ca1c0 | 2026-11-01 23:51:18 -0300 | Jozeias Fernandes de Sousa | Create Medical imaging infrastructure

cbdc90a | 2026-11-01 16:38:53 -0300 | Jozeias Fernandes de Sousa | import DICOM via MainWindow (Passo 8e)" -m "- Add 'Importar DICOM' button to the Workspace TopOverlay. - MainWindow._on_import_dicom_clicked loads DICOM, registers in   DomainObjectStore and Scene, and reloads the Workspace. - Workspace.reload_volume() iterates Editors. - TomographyEditor.reload_volume() resets and re-applies volume. - MPRView.set_volume() and Viewport3DView._ensure_pipeline()   always add the QVTKRenderWindowInteractor to the container's   layout, even when the container was already created by   content_widget(). - __main__.py configures QSurfaceFormat (depth 24, stencil 8,   OpenGL 3.2 core) and AA_ShareOpenGLContexts at module level,   before any cranioz.* import (which could create a QApplication). - AreaWidget forces a VTK render on the next event-loop iteration   to ensure the first frame is drawn. - Add integration and unit tests.
Note: TaskManager (async import) is Passo 9. SceneObjectAdded
events (reactive updates) are Passo 9

6d823be | 2026-11-01 12:13:28 -0300 | Jozeias Fernandes de Sousa | Import DICOM via MainWindow (Passo 8e)" -m "- Add 'Importar DICOM' button to the Workspace TopOverlay,   alongside the 'Home' button. - MainWindow._on_import_dicom_clicked opens QFileDialog.getExistingDirectory,   calls load_dicom_series, registers the VolumeData in the   DomainObjectStore, adds the object to the Scene, and calls   Workspace.reload_volume(). - Workspace.reload_volume() iterates Editors and calls   reload_volume() on those that support it. - TomographyEditor.reload_volume() resets _volume_applied and   calls _try_apply_volume(). - Add integration test (test_main_window_import) and unit test   (test_reload_volume).
Note: VTK OpenGL errors (wglMakeCurrent) appear in tests on
Windows without GPU. The tests pass; the errors are cosmetic.
The fix (offscreen platform or EGL) is deferred to Passo 9.
TaskManager (async import) is Passo 9. SceneObjectAdded events
(reactive updates) are Passo 9.

See ADR-0005, ADR-0006.

58fc9d8 | 2026-11-01 11:48:53 -0300 | Jozeias Fernandes de Sousa | Volume rendering with vtkSmartVolumeMapper" -m "- Add VolumePreset dataclass with 4 built-in presets   (bone, soft_tissue, skin, ct_angio). Each preset carries color   and opacity transfer function points, plus default window/level. - Replace the vtkOutlineFilter placeholder in Viewport3DView   with vtkSmartVolumeMapper + vtkVolume. The outline is kept as a   bounding box around the volume. - Add set_preset(name) and set_window_level(window, level) to   Viewport3DView. The window/level is stored (applied to the   transfer function is deferred to Passo 8d). - Add set_volume_preset(name) to TomographyEditor, delegating to   Viewport3DView. - Add tests for presets, Viewport3DView volume rendering, and   the TomographyEditor + VolumeData pipeline.
Note: preset editor, import/export, and per-user presets are
Phase 8. Window/level controls in the Toolbar are Passo 8d.

See ADR-0013, scene.md ┬º24, ┬º27.

494c089 | 2026-11-01 11:21:10 -0300 | Jozeias Fernandes de Sousa | feat(editors): real MPR and 3D views with VTK" -m "- MPRView: replace QLabel placeholder with vtkResliceImageViewer   (axial, coronal, sagittal). - Viewport3DView: replace QLabel placeholder with   QVTKRenderWindowInteractor + vtkOutlineFilter (3D outline). - TomographyEditor: resolve the first VolumeData from the   DomainObjectStore via SceneQuery and pass it to each View   via set_volume(). - Add unit tests for MPRView and Viewport3DView, and an   integration test for the TomographyEditor + DomainObjectStore   pipeline.
Note: volume rendering (vtkVolume) and isosurface
(vtkFlyingEdges3D) are deferred to Passo 8c. Window/level
controls are deferred to Passo 8d. Reactive updates via
SceneObjectAdded events are deferred to Passo 9.

See ADR-0013, scene.md.

752c439 | 2026-11-01 10:46:55 -0300 | Jozeias Fernandes de Sousa | feat(imaging): import DICOM series into the Scene" -m "- Add VolumeData (domain payload wrapping vtkImageData). - Add load_dicom_series (pydicom + vtkImageData, single axial series). - Add ImportDicomSeriesCommand and ImportDicomSeriesHandler. - Instantiate DomainObjectStore at boot and wire it through   MainWindow ÔåÆ Workspace ÔåÆ EditorContext. - Add unit tests (loader) and integration test (Command ÔåÆ Scene).
Scope (Passo 8a): one axial series, no obliquity, no multi-frame,
no DICOMDIR, no JPEG2000. Window/level, MPR and 3D views are deferred
to Passo 8b/8c. See ADR-0008, scene.md.

75d6d3a | 2026-11-01 01:28:26 -0300 | Jozeias Fernandes de Sousa | Settings Panel Documentation

943662d | 2026-10-31 11:40:43 -0300 | Jozeias Fernandes de Sousa | feat(scene): wire SceneProvider and SceneQueryAdapter through MainWindow
- Add SceneProvider Protocol and InMemorySceneProvider (reference
  implementation). The Scene is created empty; FilesystemSceneProvider
  is deferred to Phase 4 (Scene serialization).
- Add SceneQueryAdapter (implements SceneQuery, backed by the domain
  Scene). The adapter is read-only and returns object IDs, not payloads:
  resolving the actual object requires the DomainObjectStore (future
  piece). The Protocol method is renamed to get_object_id to reflect
  this contract honestly.
- MainWindow receives an optional SceneProvider, creates a
  SceneQueryAdapter per Workspace, and passes it to the Workspace. The
  underlying Scene is owned by the provider (single source of truth).
- __main__ instantiates InMemorySceneProvider and passes it to
  MainWindow.
- Add unit tests for SceneProvider and SceneQueryAdapter, and an
  integration test for the MainWindow ÔåÆ Workspace wiring.

ADR-0008, scene.md, editors.md ┬º15.

ced19f2 | 2026-10-31 00:19:46 -0300 | Jozeias Fernandes de Sousa | feat(scene): add SceneQuery and EventSubscription to EditorContext" -m "- Add SceneQuery Protocol and InMemorySceneQuery (reference implementation). SceneQuery exposes a read-only view of the Scene; all mutations go through Commands (ADR-0007). - Add scene_query and event_subscription fields to EditorContext (ADR-0002 ┬º2.1, editors.md ┬º15). - Propagate scene_query and event_subscription from MainWindow -> Workspace -> LayoutBuilder -> EditorContext. - Wire InMemorySceneQuery and EventSubscription into __main__.py. - Add integration test verifying that the Editor receives the SceneQuery via its EditorContext.
ADR-0002, ADR-0008, editors.md ┬º15.

d3858b5 | 2026-10-31 00:04:02 -0300 | Jozeias Fernandes de Sousa | feat(commands): add CommandExecutor with transaction boundary" -m "- Add TransactionManager Protocol and InMemoryTransactionManager (reference no-op implementation). - Refactor CommandExecutor to open a transaction, dispatch the Command, and commit or rollback. Events are published only after commit (the Handler is responsible for publishing; the executor ensures rollback on failure). - Add is_reversible and compensating fields to Command (ADR-0007 ┬º2.5). - Wire InMemoryTransactionManager into __main__.py. - Add unit tests for TransactionManager (commit on success, rollback on exception). - Update CommandExecutor tests (reversibility, rollback, unknown Command).
ADR-0007.

249efe9 | 2026-10-30 23:47:41 -0300 | Jozeias Fernandes de Sousa | docs(implementation): update status after ADR-0013 visual hierarchy
- Mark EditorContext propagation as resolved (┬º10.2).
- Add the visual hierarchy deliverables to Phase 4 (┬º6).
- Update the Phase 4 status and the Phase Overview table (┬º4, ┬º6).
- Mark the QTabBar centered fix as obsolete (QTabWidget removed).
- Document the VTK/MPR placeholders in ┬º10.8.
- Update the summary (┬º9).

25ed515 | 2026-10-30 23:42:48 -0300 | Jozeias Fernandes de Sousa | feat(renderer): materialize View Layout Tree as synchronized 2x2 grid" -m "- Add ViewLayoutRenderer: materializes a ViewLayoutSpec into Qt widgets. - For the common 2x2 grid pattern, use nested QSplitters with synchronized inner splitters. Dragging one inner splitter moves the other, so the columns stay aligned across rows. - For other layouts, fall back to independent nested QSplitters. - Update TomographyEditor.content_widget() to use ViewLayoutRenderer and render the 4 Views in a synchronized 2x2 grid. - Update TomographyEditor.view_layout() to a symmetric 2x2 grid. - Refactor AreaWidget._build_editor_widget to give Toolbars a Fixed size policy. - Refactor AreaWidget.refresh to call editor.dispose() before clearing the layout. - Refactor LayoutRenderer._reconcile_children to set minimum sizes, equal stretch factors, and equal initial sizes. - Replace Viewport3DView's QVTKRenderWindowInteractor with a QLabel placeholder (VTK real to be implemented later). - Update scripts/debug_workspace.py to use the real TomographyEditor. - Add unit tests for ViewLayoutRenderer and integration tests for TomographyEditor.
ADR-0013 ┬º2.4.

1784623 | 2026-10-30 23:07:27 -0300 | Jozeias Fernandes de Sousa | feat(renderer): materialize View Layout Tree as nested QSplitters" -m "- Add ViewLayoutRenderer: materializes a ViewLayoutSpec (nested split tree of Views) into QSplitters. Each Split becomes a QSplitter; each Leaf becomes the View's content_widget(). - Update TomographyEditor.content_widget() to use ViewLayoutRenderer and render the 4 Views (Axial, Coronal, Sagittal, 3D) in a symmetric 2x2 grid instead of a placeholder. - Update TomographyEditor.view_layout() to a symmetric 2x2 grid (Vertical split of two Horizontal splits), replacing the asymmetric layout. - Refactor AreaWidget._build_editor_widget to give Toolbars a Fixed size policy (LEFT/RIGHT: fixed width; TOP/BOTTOM: fixed height), preventing them from being stretched or collapsed. - Refactor AreaWidget.refresh to call editor.dispose() before clearing the layout, preventing widget leaks and stacking. - Refactor LayoutRenderer._reconcile_children and ViewLayoutRenderer._reconcile_children to set a minimum size, equal stretch factors, and equal initial sizes for all children. This prevents QSplitter from collapsing quadrants and produces a symmetric layout. - Update scripts/debug_workspace.py to use the real TomographyEditor. - Add unit tests for ViewLayoutRenderer (single leaf, horizontal/vertical splits, nested 2x2, cache reuse, clear_cache). - Add integration tests for TomographyEditor (views, view_layout structure, content widget structure, toolbars, dispose). - Update test_area_widget.py to reflect the QSplitter structure and the Toolbar-inside-Editor contract.
ADR-0013 ┬º2.4.

f40302c | 2026-10-30 10:08:38 -0300 | Jozeias Fernandes de Sousa | feat(renderer): materialize View Layout Tree as nested QSplitters" -m "- Add ViewLayoutRenderer: materializes a ViewLayoutSpec (nested split tree of Views) into QSplitters. Each Split becomes a QSplitter; each Leaf becomes the View's content_widget(). - Update TomographyEditor.content_widget() to use ViewLayoutRenderer and render the 4 Views (Axial, Coronal, Sagittal, 3D) in a 2x2 grid instead of a placeholder. - Add unit tests for ViewLayoutRenderer (single leaf, horizontal/vertical splits, nested 2x2, cache reuse, clear_cache). - Add integration tests for TomographyEditor (views, view_layout, content widget structure, toolbars, dispose).
ADR-0013 ┬º2.4.

648950d | 2026-10-30 09:51:31 -0300 | Jozeias Fernandes de Sousa | feat(editors): introduce TomographyEditor and ToolbarPosition" -m "- Add TomographyEditor (editor.tomography), which hosts the Axial, Coronal, Sagittal, and 3D Views in a 2x2 grid (ADR-0013). - Add ToolbarPosition enum (TOP, BOTTOM, LEFT, RIGHT) and the position field to ToolbarSpec (ADR-0013 ┬º2.6). - Register TomographyEditor in __main__.py. - Update WorkspaceSpec.DEFAULT to use editor.tomography instead of the placeholder editor. - Update test_main_window.py fixture to register TomographyEditor. - Refactor AreaWidget to render the Editor Layout Tree as nested QSplitters, removing the QTabWidget (ADR-0013 ┬º2.2). - Move the Toolbar inside the Editor container, honoring ADR-0002 ┬º2.2 and ADR-0013 ┬º2.6. - Update test_area_widget.py to reflect the QSplitter structure and the Toolbar-inside-Editor contract.
This resolves the original problem: tabs consumed vertical space in the Central Area. The split tree scales to 2x2, 4x2, and beyond.

3d3b108 | 2026-10-30 09:39:29 -0300 | Jozeias Fernandes de Sousa | feat(editors): introduce TomographyEditor and ToolbarPosition
- Add TomographyEditor (editor.tomography), which hosts the Axial,
  Coronal, Sagittal, and 3D Views in a 2x2 grid (ADR-0013).
- Add ToolbarPosition enum (TOP, BOTTOM, LEFT, RIGHT) and the
  `position` field to ToolbarSpec (ADR-0013 ┬º2.6).
- Register TomographyEditor in __main__.py.
- Update WorkspaceSpec.DEFAULT to use editor.tomography instead of
  the placeholder editor.
- Update test_main_window.py fixture to register TomographyEditor.

This is the first real Editor. It hosts its Views internally, per
ADR-0013. The next piece (Passo 3) will refactor AreaWidget to
render the Editor Layout Tree as nested QSplitters instead of
QTabWidget.

c15947d | 2026-10-30 09:27:17 -0300 | Jozeias Fernandes de Sousa | feat(ui): introduce View abstraction and ViewLayoutSpec
- Add `View` ABC (view_id, view_type, content_widget, dispose).
- Add `ViewLayoutSpec` (nested split tree for View layout).
- Update `Editor` ABC with `views()` and `view_layout()`.
- Rename `Viewport3DEditor` ÔåÆ `Viewport3DView` (now a View).
- Rename `MPRViewerEditor` ÔåÆ `MPRView` (now a View).
- Update `__main__.py` to register the Views temporarily.

This is the foundation for the TomographyEditor (Passo 2), which
will host these Views in a 2x2 grid.

ADR-0013.

90b87e7 | 2026-10-30 09:02:46 -0300 | Jozeias Fernandes de Sousa | @" docs(adr): add ADR-0013 Editor Layout Tree, View Layout Tree, and Toolbar Placement
- Define the four-level hierarchy: Workspace ÔåÆ Area ÔåÆ Editor ÔåÆ View.
- Editor Layout Tree is rendered as nested QSplitters, not QTabWidget.
- View is a first-class concept: Viewport3D and MPR are Views, not
  Editors. The TomographyEditor and CephalometryEditor host them.
- ToolbarSpec gains a ``position`` field (LEFT, RIGHT, TOP, BOTTOM),
  allowing Editors to declare Toolbars on any side.
- Editor Stack (switcher) is the preferred presentation for stacking
  multiple Editors in the same Leaf (replaces tabs).
- Clarifies ADR-0001: the prototype is illustrative, not normative.
- Completes ADR-0002: specifies where Toolbars sit inside the Editor.

This ADR is the foundation for the Phase 4 refactoring:
- AreaWidget: QTabWidget ÔåÆ QSplitter.
- Viewport3DEditor/MPRViewerEditor ÔåÆ Viewport3DView/MPRView.
- Introduce TomographyEditor and CephalometryEditor as View hosts.
"@ | Out-File -FilePath commit_msg.txt -Encoding utf8

git commit -F commit_msg.txt

Remove-Item commit_msg.txt

5efbcca | 2026-10-29 23:51:54 -0300 | Jozeias Fernandes de Sousa | fix(rendering): resolve ruff and mypy errors in VTK placeholders
- vtk_actor_factory: defer `import vtk` to `create_mesh_actor`
  with `# noqa: PLC0415` to preserve VTK optionality; add
  `from exc` to RuntimeError (B904); remove dead `_logger` and
  redundant top-level try/except (F401, B904).
- vtk_scene_renderer: restore `__init__` (was accidentally
  removed) and re-add ActorRegistry/VTKActorFactory/Scene imports;
  defer `import vtk` to `__init__` with `# noqa: PLC0415`;
  add `from exc` to RuntimeError (B904).
- viewport_3d/editor: add `# noqa: PLC0415` to deferred VTK
  imports; add `from exc` to RuntimeError (B904); add
  `# type: ignore[no-untyped-call]` to QVTKRenderWindowInteractor
  and GetRenderWindow calls (mypy).

CI is now green:
- ruff check: 0 errors
- ruff format: clean
- mypy: 0 errors in 224 source files
- pytest: 1093 passed

aa122c5 | 2026-10-29 22:11:02 -0300 | Jozeias Fernandes de Sousa | feat(scene): implement Scene, DomainObjectStore, and Commands
- Add Transform, Vector3, Quaternion (rigid transformation).
- Add SpatialRelationship (typed link between objects).
- Add DomainObjectStore (Project-scoped canonical registry).
- Add Scene (membership, hierarchy, transforms, relationships).
- Add Scene Commands (Add/Remove/Transform/SetParent/AddRelationship).
- Add Scene CommandHandlers.
- Add JSON serialization (schema_version=1).
- Add unit tests for all components.
- Fix ruff/mypy errors (contextlib.suppress, kw_only, str|None).

Verification:
- Tests: 1086 passed in 8.89s
- mypy: 213 source files, no issues
- ruff: all checks passed

Closes ┬º5.1.5 of implementation.md (domain/scene/).

830abe7 | 2026-10-29 19:58:30 -0300 | Jozeias Fernandes de Sousa | fix(workspace): close Phase 2 and complete EditorContext propagation
Phase 2 (lifecycle, geometry, debug visual) is fully resolved:
- AreaWidget.refresh() preserves Editor content_widget() across re-renders.
- LayoutRenderer.compute_region_bounds() maps to Workspace coordinates.
- Workspace.clear() calls Editor.dispose() and clear_cache().
- Workspace.load_spec() is atomic (build ÔåÆ clear ÔåÆ render ÔåÆ install).
- Workspace.showEvent() (inside the class) repositions overlays after
  the layout is computed.
- QTabBar is centered via stylesheet.
- DebugEditor (no toolbars) cleans up the debug visual.

EditorContext propagation (ADR-0002 ┬º2.3):
- LayoutBuilder.build() propagates shared_context by reference.
- _instantiate_editors() passes **shared to EditorContext.
- Workspace.load_spec() passes task_manager and telemetry.
- EditorContext field order fixed (editor_id first).

Tests:
- test_top_overlay_is_positioned_over_central_area (deterministic)
- test_build_propagates_shared_context_to_each_editor
- test_area_widget_refresh_preserves_editor_content
- test_workspace_clear_calls_editor_dispose
- test_load_spec_atomic_on_failure

Verification:
- Tests: 1063 passed in 4.15s
- mypy: 199 source files, no issues
- ruff: all checks passed
- Visual verification: debug_workspace.py shows TopOverlay aligned
  with Central Area, tabs centered, no toolbars polluting.

9642c03 | 2026-10-29 19:20:57 -0300 | Jozeias Fernandes de Sousa | feat(telemetry): implement LoggingTelemetrySink
- Create LoggingTelemetrySink adapter in infrastructure/telemetry/.
- Wire it into __main__.py (replaces NoOpTelemetrySink).
- Add contract tests for TelemetrySink (events, measurements,
  severity mapping, correlation_id).
- Update implementation.md ┬º5.1.1: mark as complete.

This is Step 1 of ┬º5.1 in implementation.md.

Tests: 1063 passed in 8.85s
mypy: 199 source files, no issues
ruff: all checks passed

1860394 | 2026-10-29 19:11:45 -0300 | Jozeias Fernandes de Sousa | Closes ┬º10.1 of implementation.md. All Phase 2 bugs are fixed:
Fixes:
- AreaWidget.refresh() preserves Editor content_widget() across
  re-renders (cache + detach before container deletion).
- LayoutRenderer.compute_region_bounds() maps AreaWidget geometries
  to Workspace coordinates via mapTo(workspace, ...).
- Workspace.clear() calls Editor.dispose() before widget deletion.
- Workspace.load_spec() is atomic (build first, then clear).
- LayoutRenderer connects QSplitter.splitterMoved to Workspace's
  _reposition_overlays(), so the TopOverlay follows manual resizes.
- QTabBar is centered via stylesheet ('alignment: center').
- Removed erroneous QPoint.isValid() check.
- test_editor.py: removed duplicate toolbar_specs(), added
  DebugEditor with explicit typed __init__.
- debug_workspace.py: uses DebugEditor (no Log/Toggle buttons).

Tests:
- test_top_overlay_is_positioned_over_central_area (new)
- test_area_widget_refresh_preserves_editor_content (new)
- test_workspace_clear_calls_editor_dispose (new)
- test_load_spec_atomic_on_failure (new)

Verification:
- Tests: 1055 passed in 10.30s
- mypy: 197 source files, no issues
- ruff: all checks passed

Visual verification: debug_workspace.py shows the TopOverlay
aligned with the Central Area, tabs centered, no toolbars
polluting the visual, and all Areas with their debug colors.

fddec12 | 2026-10-29 18:10:28 -0300 | Jozeias Fernandes de Sousa | fix(workspace): resolve Phase 2 lifecycle and geometry debt
Fixes:
- AreaWidget.refresh() preserves Editor content_widget() across
  re-renders by caching and detaching it before container deletion.
  Prevents RuntimeError: Internal C++ object already deleted.
- LayoutRenderer.compute_region_bounds() maps each AreaWidget's
  geometry to Workspace coordinates via mapTo(workspace, ...),
  fixing the TopOverlay misalignment observed in debug_workspace.py.
- Workspace.clear() calls Editor.dispose() before widget deletion,
  releasing Tasks, subscriptions, and other Editor-owned resources.
- Workspace.load_spec() builds and renders the new composition
  before tearing down the old one (atomicity).
- Removed erroneous QPoint.isValid() check (QPoint has no such
  method; QPointF does).
- Moved _logger definitions after imports to satisfy E402.
- Applied ruff format to repetitive_commands.md.

Verification:
- Tests: 1053 passed in 9.23s
- mypy: 197 source files, no issues
- ruff: all checks passed

Closes the four bugs documented in implementation.md ┬º10.1.

ce4deec | 2026-10-29 12:41:56 -0300 | Jozeias Fernandes de Sousa | New configurations of environment.
- Replace 'type: ignore[misc]' with explicit runtime validation
- Log errors for invalid payload/callback/args
- Align with Principle #17 (Errors Are Information, Not Failures)

66c5c1b | 2026-10-24 10:12:27 -0300 | Jozeias Fernandes de Sousa | .

431cfff | 2026-10-23 10:52:24 -0300 | Jozeias Fernandes de Sousa | - FlowList.set_flows sorts flows by flow_id before rendering. The order   is independent of filesystem iterdir(). When the flow schema gains an   'order' field, this sort is the single place to change. - Add test_set_flows_sorts_by_flow_id covering the render-order contract. - Document FlowRow horizontal overflow as known debt in   implementation.md ┬º10.8; the UX decision belongs to Phase 5. - Bump ruff minimum to >=0.16 in pyproject.toml to match the tested   baseline. - Format the two touched files with ruff format.
Note: 'ruff format --check .' panics on Ruff 0.16.9 with
'Annotation range 0..308 is beyond the end of buffer 306' on large
aggregate diffs, and reports would-reformat on files formatted for an
older Ruff. The panic is a Ruff diagnostic-renderer bug; the
would-reformat findings are formatting-only under the new baseline.
A global reformatting piece is tracked in implementation.md ┬º10.11."

2630ef0 | 2026-10-23 09:44:28 -0300 | Jozeias Fernandes de Sousa | feat(flows): redesign FlowList and populate from FlowCatalog
A4 (FlowList redesigned):
- FlowRow (new widget): renders a flow as a horizontal row of steps
  connected by arrows. Clicking toggles the flow's checked state and
  emits selected(flow_id) or selected(None).
- FlowList rewritten: renders each flow as a FlowRow. Only one row is
  checked at a time (mutual exclusion). set_flows now receives
  tuple[FlowDefinition, ...] instead of list[tuple[str, str]].
  set_flows clears any existing selection and emits flow_selected(None)
  to keep the caller's state consistent.
- HomePage accepts an optional flow_list_translate callable and
  forwards it to FlowList. Default is identity.

A5 (populate from catalog):
- FlowCatalog.list_definitions(): returns full FlowDefinition objects
  for all flows in the catalog.
- MainWindow accepts an optional flow_catalog. When provided, populates
  the HomePage's FlowList at construction; on catalog failure, logs and
  leaves the placeholder.
- __main__ constructs FilesystemFlowRepository(flows_root=...),
  FlowCatalog(repository=...), and passes flow_catalog to MainWindow.
  The 3 flows from ~/Documents/CranioZ/Flows/ (seeded by
  scripts/seed_flows.py) appear as horizontal rows.

Tests: 7 (FlowRow), 7 (FlowList), 20 (HomePage updated),
1 (Catalog list_definitions). Full suite: 1036 passed.
Ruff: All checks passed. Mypy: Success, 195 source files.

9ca7959 | 2026-10-23 08:05:31 -0300 | Jozeias Fernandes de Sousa | feat(flows): add Flow domain, filesystem adapter, and seed script
application/flows:
- FlowDefinition, FlowStep: immutable declarative flow content.
- FlowSummary: lightweight projection for the Home Page.
- FlowRepository (Protocol), InMemoryFlowRepository (reference).
- FlowCatalog: read-only projection (list, get, search).
- FlowError, FlowNotFound, FlowCorrupted, FlowStorageError.

infrastructure/flows:
- FlowPathResolver: validates flow_id as a safe path segment.
- flow_serialization: pure JSON round-trip.
- FilesystemFlowRepository: reads <flows_root>/<flow_id>/flow.json.
  Translates I/O to FlowError. Skips corrupted entries in list.

scripts/seed_flows.py:
- Idempotent creation of 3 example flows under
  ~/Documents/CranioZ/Flows/: orthognathic_basic,
  orthognathic_advanced, facial_implants.

The catalog is not wired into the Home Page yet; the FlowList still
uses the placeholder hardcoded data from debug scripts. The next
piece (A4/A5) redesigns FlowList and populates it from
FlowCatalog.list_flows().

Tests: 23 new. Full suite: 1028 passed.
Ruff: All checks passed. Mypy: Success, 194 source files.

914a03b | 2026-10-23 00:03:30 -0300 | Jozeias Fernandes de Sousa | feat(ui): wire TaskManager and TelemetrySink through MainWindow ÔåÆ Workspace
- EditorContext gains task_manager, telemetry, and correlation_id (all
  optional).
- Workspace accepts task_manager and telemetry at construction, exposes
  task_manager() and telemetry() accessors.
- MainWindow forwards TaskManager and TelemetrySink from the bootstrap
  to the Workspace (ADR-0006 ┬º2.5: no rules in MainWindow, only
  forwarding).
- __main__.py constructs InMemoryCommandBus, NoOpTaskManager,
  NoOpTelemetrySink, EventBusAdapter, InMemoryModuleRegistry, and
  registers BUILTIN_MANIFESTS (currently empty). All are injected into
  the MainWindow.
- Fix E501 in main_window.py (line wrapping only, no behavior change).

App verified end-to-end: Home Page with 5 projects and 3 flows,
StartButton disabled until both are selected, Workspace with Home
button and placeholder editor, Home button returns to Home Page.

Tests: 983 passed. Ruff: All checks passed. Mypy: Success, 183 source
files.

1df013e | 2026-10-22 23:52:44 -0300 | Jozeias Fernandes de Sousa | feat(application,modules): complete Phase 4 contracts
Application layer (5 packages):
- application/commands: Command, CommandHandler, CommandBus,
  CommandStack, InMemoryCommandBus, InMemoryCommandStack.
- application/tasks: Task, TaskHandle, TaskManager, CancelToken,
  TaskState, NoOpTaskManager.
- application/telemetry: TelemetrySink, Severity, MeasurementUnit,
  TELEMETRY_RESERVED_EVENTS, TELEMETRY_RESERVED_MEASUREMENTS,
  NoOpTelemetrySink, RecordingTelemetrySink.
- application/events: EventSubscription, EventPublisher,
  SubscriptionHandle, EventBusAdapter.
- application/services: ServiceContainer, EmptyServiceContainer.

Modules layer (base, registry, loader):
- modules/base/module.py: Module Protocol + ModuleBase.
- modules/base/module_context.py: ModuleContext (9 fields, frozen).
- modules/base/module_manifest.py: ModuleManifest, ModuleDependency.
- modules/base/module_state.py: ModuleState enum.
- modules/registry/module_registry.py: ModuleRegistry Protocol +
  InMemoryModuleRegistry (with state tracking).
- modules/loader/module_loader.py: ModuleLoader Protocol +
  InMemoryModuleLoader (with rollback, dependency refusal).
- modules/errors.py: ModuleError family.

Sem Qt dependency na Application layer. O ModuleLoader ├® uma
refer├¬ncia (recebe inst├óncias), n├úo faz import. O PackageModuleLoader
(loader real com importlib) e o QtTaskManager/QtTelemetrySink ficam
para pe├ºas separadas.

Tests: 119 new contract tests. Full suite: 983 passed.

Ruff/Mypy:
- ruff check .: All checks passed.
- mypy src/cranioz: Success, 183 source files.

818e2dc | 2026-10-22 23:52:36 -0300 | Jozeias Fernandes de Sousa | feat(application,modules): complete Phase 4 contracts
Application layer (5 packages):
- application/commands: Command, CommandHandler, CommandBus,
  CommandStack, InMemoryCommandBus, InMemoryCommandStack.
- application/tasks: Task, TaskHandle, TaskManager, CancelToken,
  TaskState, NoOpTaskManager.
- application/telemetry: TelemetrySink, Severity, MeasurementUnit,
  TELEMETRY_RESERVED_EVENTS, TELEMETRY_RESERVED_MEASUREMENTS,
  NoOpTelemetrySink, RecordingTelemetrySink.
- application/events: EventSubscription, EventPublisher,
  SubscriptionHandle, EventBusAdapter.
- application/services: ServiceContainer, EmptyServiceContainer.

Modules layer (base, registry, loader):
- modules/base/module.py: Module Protocol + ModuleBase.
- modules/base/module_context.py: ModuleContext (9 fields, frozen).
- modules/base/module_manifest.py: ModuleManifest, ModuleDependency.
- modules/base/module_state.py: ModuleState enum.
- modules/registry/module_registry.py: ModuleRegistry Protocol +
  InMemoryModuleRegistry (with state tracking).
- modules/loader/module_loader.py: ModuleLoader Protocol +
  InMemoryModuleLoader (with rollback, dependency refusal).
- modules/errors.py: ModuleError family.

Sem Qt dependency na Application layer. O ModuleLoader ├® uma
refer├¬ncia (recebe inst├óncias), n├úo faz import. O PackageModuleLoader
(loader real com importlib) e o QtTaskManager/QtTelemetrySink ficam
para pe├ºas separadas.

Tests: 119 new contract tests. Full suite: 983 passed.

Ruff/Mypy:
- ruff check .: All checks passed.
- mypy src/cranioz: Success, 183 source files.

12a6902 | 2026-10-22 23:32:09 -0300 | Jozeias Fernandes de Sousa | feat(application): add Events facade contract (ADR-0007, ADR-0012)
application/events:
- EventSubscription Protocol: scoped subscription facade.
  subscribe(...) returns a SubscriptionHandle. dispose() cancels all
  handles created through the facade. After dispose, subscribe raises
  SubscriptionClosed.
- EventPublisher Protocol: publish-only facade.
- SubscriptionHandle Protocol: cancel() is idempotent.
- EventBusAdapter: wraps the existing EventBus with
  create_subscription() and create_publisher(). Each subscription is
  an independent scope.
- SubscriptionClosed, EventPublicationError: application-level errors.
- publish() logs subscriber failures and does not raise (fire-and-forget,
  ADR-0012 ┬º2.2).

The package does not replace the EventBus. The EventBus remains the
single dispatch mechanism; the facade adds scope and the
subscribe/publish split.

Tests: 13 new contract tests. Full suite: 954 passed.

Ruff/Mypy:
- ruff check .: All checks passed.
- mypy src/cranioz: Success, 180 source files.

11693dc | 2026-10-22 23:19:28 -0300 | Jozeias Fernandes de Sousa | feat(application): add Tasks and Telemetry contracts (ADR-0011, ADR-0012)
application/tasks:
- Task, TaskHandle, TaskManager, CancelToken Protocols.
- TaskState enum (PENDING, RUNNING, CANCELLING, CANCELLED, COMPLETED,
  FAILED).
- TaskError, TaskAlreadyDispatched, TaskCancelled.
- NoOpTaskManager: reference implementation. Runs Tasks synchronously
  on the caller's thread. Delivers on_progress/on_result/on_error/
  on_cancel on the caller's thread. Relaunches Task.run exceptions
  when on_error is absent. Raises TaskAlreadyDispatched on repeated
  dispatch.

application/telemetry:
- TelemetrySink Protocol with record_event and record_measurement.
  Every event and measurement carries a correlation_id.
- Severity and MeasurementUnit enums.
- TELEMETRY_RESERVED_EVENTS (21 names) and TELEMETRY_RESERVED_MEASUREMENTS
  (7 names) from ADR-0012 ┬º2.4-┬º2.5.
- TelemetryError base.
- NoOpTelemetrySink: discards everything.
- RecordingTelemetrySink: captures RecordedEvent and RecordedMeasurement
  in lists, with attributes copied and clear() between assertions.

Both packages have no Qt dependency. The concrete QtTaskManager and
LoggingTelemetrySink live in infrastructure/ and are delivered in
later pieces.

Tests: 43 new contract tests. Full suite: 941 passed.

Ruff/Mypy:
- 26 auto-fixable issues resolved (newlines, unused imports, import
  order).
- ruff check .: All checks passed.
- mypy src/cranioz: Success, 176 source files.

a40bf59 | 2026-10-22 19:52:26 -0300 | Jozeias Fernandes de Sousa | feat(application): add Commands contract (ADR-0007)
application/commands:
- Command: immutable data with command_id and metadata.
- CommandHandler: Protocol for handling a specific Command type.
- CommandBus / CommandHandlerRegistry: Protocols for routing and
  registration.
- InMemoryCommandBus: reference implementation. Synchronous dispatch,
  wraps Handler exceptions in CommandDispatchError with __cause__
  preserved.
- CommandStack / InMemoryCommandStack: undo/redo tracking.
- CommandError and subclasses: CommandNotRegistered,
  CommandDispatchError.

The package has no Qt dependency. Transaction boundaries, event
publication, and undo/redo integration are the Handler's (or a future
CommandExecutor's) responsibility.

modules/base/module_manifest:
- ModuleManifest: declarative metadata for a Module (modules.md v10 ┬º5).
- ModuleDependency: hard dependency on another Module.
- Both frozen dataclasses with structural validation.

modules/builtin/orthognathic_guide:
- Rename guide_builder -> orthognathic_guide (ambiguity: guide types
  for dental, facial, reconstruction, rhinoplasty are separate modules).
- Declare MANIFEST with module_id="orthognathic_guide", dependencies on
  osteotomies and cephalometry, entry_point for the future
  OrthognathicGuideModule.

modules/builtin/__init__:
- BUILTIN_MANIFESTS populated (empty for now; entries added as each
  module is implemented).

Tests: 34 new contract tests for Commands (base, bus, stack).
Full suite: 898 passed.

Ruff/Mypy:
- 13 auto-fixable issues resolved (newlines, unused imports in
  scripts, import order in manifest.py, unused noqa in __main__.py).
- "UP046" and "PLC0105" added to the Ruff ignore list.
- mypy src/cranioz: Success, 169 source files checked.
- ruff check .: All checks passed.

e2879d3 | 2026-10-22 19:15:07 -0300 | Jozeias Fernandes de Sousa | feat(boot,docs): open MainWindow on startup; add ADRs 0007-0012
Boot and UI:
- Wire __main__ to MainWindow: construct FilesystemProjectRepository,
  ProjectCatalog, ProjectManager, EditorRegistry, ToolRegistry, and
  ThemeService at boot, and show the window before entering the Qt
  event loop.
- Handle AppPathInaccessible with QMessageBox.critical.
- Resolve the actor from the OS username (getpass.getuser).
- Register LogTool and ToggleTool at boot.
- Build ThemeService from configuration.app.theme, falling back to DARK.
- Fix ProjectTable to emit project_selected(None) on deselection,
  preserve the selection through refresh, and block intermediate
  signals during repopulation.
- Accept ProjectId | None in HomePage._on_project_selected, matching
  the signal contract.

Development tooling:
- scripts/seed_projects.py: idempotent creation of 5 fake projects in
  the filesystem repository, for manual testing of the Home Page.
- scripts/debug_full_cycle.py: logic-only exercise of the
  Home -> Workspace -> Home cycle via ProjectManager.
- scripts/debug_workspace.py: fixed to pass the ProjectContext that
  the Workspace now requires (ADR-0006).

ADRs:
- ADR-0007: Commands, Transactions, and Undo/Redo.
- ADR-0008: Scene and DomainObjectStore.
- ADR-0009: Project Persistence Format.
- ADR-0010: Layout Persistence.
- ADR-0011: Threading and Task Execution (TaskManager contract).
- ADR-0012: Telemetry and Observability (TelemetrySink contract).

Architecture docs:
- modules.md (v10): Module contract. ModuleContext gains task_manager
  and correlation_id; activation cancels module-scoped Tasks;
  telemetry emissions are fire-and-forget; threading and telemetry
  details deferred to ADR-0011 and ADR-0012.
- editors.md: EditorContext gains task_manager, correlation_id, and
  telemetry. ┬º15.1 defines the Editor-owned Task lifecycle (cancel on
  deactivate/dispose). ┬º15.2 defines Editor telemetry.
- main_window.md: MainWindow forwards TaskManager and TelemetrySink
  to the Workspace; ┬º7.3 defines shutdown ordering; ┬º8 state
  ownership updated.
- workspace.md: ┬º3.4 splits sync and async data paths; ┬º5.6 clarifies
  layout persistence vs. telemetry; ┬º8 adds Task lifecycle; ┬º9 adds
  Workspace telemetry (reserved events and measurements).
- implementation.md: real status of Phases 0-4, Done/Pending column,
  Current Focus section.

Tests: 864 passing (8 new regression tests for ProjectTable and
HomePage deselection behavior).

This commit does not add runtime code for commands, tasks, or
telemetry. It adds the contracts (ADRs 0007-0012) and the boot wiring
that the next implementation step (application/commands,
application/tasks, application/telemetry) will satisfy.

a0c1735 | 2026-10-22 18:41:46 -0300 | Jozeias Fernandes de Sousa | docs(modules): add Module contract v9
Add the Module contract specification to docs/architecture/modules/.

- Defines module identity, lifecycle, manifest, and dependency resolution.
- Specifies the load/unload atomicity contract: per-module rollback,
  exact registration handles, and the rule that load/unload never
  leave a Module partially registered.
- Clarifies the ModuleContext boundary: event_subscription (stable
  proxy, activation-scoped), event_publisher, command_bus,
  project_provider, services, telemetry. No raw EventBus access.
- Specifies activation as the Application layer's responsibility,
  with atomic Workspace replacement and restoration of the previous
  spec on failure. Activation failures never mark a Module failed.
- Defines the error hierarchy (ModuleError and subclasses) and the
  state-after-error matrix (single source of truth).
- Notes the deferred concerns: plugin isolation, optional dependencies,
  module-owned persistence, access control, and TaskManager threading
  (see ADR-0011, ADR-0012).

The document is a self-contained contract; future ADRs (threading,
telemetry, plugin loading) reference it without redefining it.

132a7f7 | 2026-10-22 12:33:14 -0300 | Jozeias Fernandes de Sousa | fix(home): emit None from ProjectTable on deselection
The ProjectTable only emitted project_selected when a row was
selected. Clearing the selection (explicit deselection, or the
selected project filtered out by the search box) left
HomePage._selected_project_id stale and the StartButton green.

- ProjectTable._on_selection_changed now always emits the current
  selection, including None.
- ProjectTable._populate preserves the selection when the same
  project id survives a refresh, emits None only when it is gone,
  and uses blockSignals() during the rebuild to avoid an
  intermediate None -> id flicker on every refresh.
- HomePage._on_project_selected accepts ProjectId | None,
  mirroring the signal contract.
- Add regression tests at both levels: ProjectTable (unit, 6 new)
  and HomePage (integration, 2 new). All UI home tests pass.

Fixes: StartButton stayed enabled after deselection or search
filtering the selected project away.

becb59a | 2026-10-22 11:42:19 -0300 | Jozeias Fernandes de Sousa | feat(boot): wire __main__ to MainWindow
- Construct FilesystemProjectRepository, ProjectCatalog, ProjectManager
  from the initialized AppPathResolver.
- Register LogTool and ToggleTool in the ToolRegistry at boot.
- Build the ThemeService from configuration.app.theme, with a DARK
  fallback for unknown values.
- Resolve the actor via getpass.getuser(), with a "local-user"
  fallback.
- Instantiate and show MainWindow; the application now has a visible
  top-level window when started with `python -m cranioz`.
- Handle AppPathInaccessible with QMessageBox.critical instead of
  letting the exception crash the process before the Qt event loop.
- Update the module docstring to reflect the actual boot sequence.

Fixes: `python -m cranioz` entered app.exec() with no window, so the
process appeared to hang and no UI was visible.

80b4fbb | 2026-10-22 10:35:30 -0300 | Jozeias Fernandes de Sousa | fix(home): emit None from ProjectTable on deselection
The ProjectTable only emitted project_selected when a row was
selected. Clearing the selection (explicit deselection, or the
selected project filtered out by the search box) left
HomePage._selected_project_id stale and the StartButton green.

- ProjectTable._on_selection_changed now always emits the current
  selection, including None.
- ProjectTable._populate preserves the selection when the same
  project id survives a refresh, emits None only when it is gone,
  and uses blockSignals() during the rebuild to avoid an
  intermediate None -> id flicker on every refresh.
- HomePage._on_project_selected accepts ProjectId | None,
  mirroring the signal contract. Signal comment updated to
  ProjectId | None.
- Add regression tests at both levels: ProjectTable (unit, 6 new)
  and HomePage (integration, 2 new). All 77 UI tests pass.

Fixes: StartButton stayed enabled after deselection or search
filtering the selected project away.

a7d42a2 | 2026-10-22 10:13:19 -0300 | Jozeias Fernandes de Sousa | feat(ui): complete Bloco 7 with MainWindow navigation (piece 7.6b)
MainWindow is the application shell. It hosts the HomePage and the
Workspace in a QStackedWidget, and it is the sole orchestrator of
navigation between them (ADR-0006).

Navigation flow:

- HomePage.project_open_requested(project_id, flow_id)
  -> MainWindow._on_project_open_requested
  -> ProjectManager.open_project(actor, project_id,
                                 workflow_id=flow_id,
                                 workflow_config={})
  -> Workspace(project_context=...)
  -> inject "Home" button into TopOverlay via set_left_content
  -> workspace.load_spec(WORKSPACE_SPEC_DEFAULT)
  -> stack.setCurrentWidget(workspace)

- "Home" button clicked
  -> MainWindow._on_home_clicked
  -> ProjectManager.close_project(actor, project_id)
  -> destroy Workspace (deleteLater)
  -> stack.setCurrentWidget(home)
  -> home.refresh()

Production changes:

- TopOverlay.set_left_content(widget). The TopOverlay stays a
  generic container (ADR-0006). Per-segment QHBoxLayouts ready
  for content.

- Workspace requires project_context (keyword-only). WorkspaceError
  if None. The Workspace does not orchestrate its own lifecycle.

- WorkspaceSpec.DEFAULT: a single Central Area with a real
  _PlaceholderEditor (inherits from Editor, not DummyEditor) that
  shows "No flow loaded" centered. No toolbar, no leaked editor_id.

- StartButton objectName changed from "home_page.start_button" to
  "home_page_start_button". Qt Style Sheets treat "." as a class
  separator; the previous selector never matched. The button now
  renders grey (disabled) / green (enabled) as designed.

- MainWindow and Workspace constructors are keyword-only
  (ruff PLR0917: too many positional arguments).

- MainWindow placeholder handlers (new_project_requested,
  manage_projects_requested, manage_flows_requested,
  settings_requested, help_requested, community, library, news,
  feedback, contribute) show QMessageBox.information referencing
  the future piece.

Documentation:

- ADR-0006 records the navigation and window-lifecycle boundaries.
- workspace.md ┬º6.2, ┬º6.3, ┬º7.1 gain notes pointing to ADR-0006.

Tests: 856 passed. Ruff: All checks passed. Mypy: Success.

Bloco 7 is functionally closed:
7.1 ProjectRepository (Protocol) + contract tests + InMemory impl
7.2 ProjectContext + lifecycle events
7.3 FilesystemProjectRepository + serialization
7.4 ProjectCatalog (read model)
7.5 ProjectManager + ProjectAccessPolicy
7.6a HomePage + sub-widgets
7.6b MainWindow + Home<->Workspace navigation

1a4765d | 2026-10-20 15:25:12 -0300 | Jozeias Fernandes de Sousa | docs(adr): add ADR-0006 MainWindow navigation orchestrator
Formalizes the navigation and window-lifecycle boundaries adopted
in piece 7.6b:

- The "Home" button is a navigation link that emits clicked(). It
  does not call close_project or destroy the Workspace.
- MainWindow is the sole orchestrator of Home<->Workspace
  navigation. It calls ProjectManager, creates/destroys the
  Workspace, and returns to HomePage.
- TopOverlay is a generic container. set_left_content(widget) is
  the injection point; set_center_content and set_right_content
  are deferred to piece 7.6c.
- Workspace receives ProjectContext at construction. It does not
  orchestrate its own lifecycle.
- ProjectManager does not import Qt and does not create/destroy
  widgets.
- MainWindow receives ProjectManager and Actor at construction.

Also adds three notes to workspace.md (┬º6.2, ┬º6.3, ┬º7.1)
pointing to ADR-0006.

eb1f18b | 2026-10-20 10:30:27 -0300 | Jozeias Fernandes de Sousa | feat(ui): add HomePage and sub-widgets (piece 7.6a)
HomePage is the entry point and project discovery screen
(home_page.md ┬º1-┬º3, ┬º22). It is a presentation and dispatch
layer: it lists projects and flows, and emits signals for every
user intention. It does not create, delete, or open projects;
the MainWindow (piece 7.6b) listens to those signals and calls
the Application services.

Layout (proportional, not draggable):

    HomePage
    ÔööÔöÇÔöÇ QHBoxLayout
        Ôö£ÔöÇÔöÇ CommunitySidebar (200 px, hidden by default, full height)
        ÔööÔöÇÔöÇ QVBoxLayout (stretch 8 / 42 / 42 / 8)
            Ôö£ÔöÇÔöÇ HomeTopBar       (~8%)
            Ôö£ÔöÇÔöÇ ProjectTable     (~42%)
            Ôö£ÔöÇÔöÇ FlowList         (~42%)
            ÔööÔöÇÔöÇ HomeBottomBar    (~8%)
                ÔööÔöÇÔöÇ StartButton (aligned right)

No QSplitter: the prototype shows fixed panels. If per-user
proportions are ever needed, that is a separate piece (LayoutState
persistence). setMinimumHeight on the top and bottom bars protects
against very small windows.

Sub-widgets:
- HomeTopBar: menu (Ôÿ░), title, help, settings. The Ôÿ░ toggles the
  CommunitySidebar; it does not open an application menu.
- CommunitySidebar: community, library, news, feedback, contribute.
  Hidden by default; fills the full height (vertical Expanding).
- ProjectTable: Nome, ID, Sexo, Idade, Cria├º├úo do projeto, ├Ültima
  modifica├º├úo. QTableWidget, not QTableView + model. Sexo/Idade
  show em-dash placeholder (ProjectSummary does not carry them).
- FlowList: empty until Bloco 9. Placeholder removal depends only
  on the presence of flows.
- HomeBottomBar: hosts the StartButton.

Buttons:
- "Novo projeto" ÔåÆ new_project_requested().
- "Gerir projetos" ÔåÆ manage_projects_requested(). Replaces the
  previous "Remover projeto". Rationale: destructive operations
  belong in a management page, not in the discovery screen.
- "Gerir Fluxos" ÔåÆ manage_flows_requested().
- StartButton: grey by default; green only when both a project
  and a flow are selected. Clicking emits
  project_open_requested(project_id, flow_id).

Architectural boundary:
- HomePage.__init__ receives only ProjectCatalog. It does not
  receive ProjectManager. test_home_page_has_no_project_manager_reference
  enforces this contract.

Documentation:
- home_page.md ┬º25 updated (HomeBottomBar, not FAB).
- "Recent projects" deferred to piece 7.6d.

Known debt (deferred):
- Theme (7.6d): HomePage uses Qt Fusion default palette (dark).
- StartButton visual (Icon Manager): inline QSS + unicode "ÔåÆ"
  will be replaced by an SVG via ThemeService.icon("start").
- Search field icon, expand button, rounded buttons (Icon Manager).
- "Recent projects" section (7.6d).

Tests: 829 passed. Ruff: All checks passed. Mypy: Success.

2a4a8d6 | 2026-10-20 00:23:37 -0300 | Jozeias Fernandes de Sousa | feat(ui): add HomePage and sub-widgets (piece 7.6a)
HomePage is the entry point and project discovery screen
(home_page.md ┬º1-┬º3, ┬º22). It is a presentation and dispatch
layer: it displays projects and flows, and emits signals for
every user intention. It does not create, delete, or open
projects; the MainWindow (piece 7.6b) listens to those signals
and calls the Application services.

Composition:
- HomePage composes four sub-widgets plus a floating action button:
  * HomeTopBar (menu, title, help, settings)
  * CommunitySidebar (community, library, news, feedback, contribute)
  * ProjectTable (list, search, new/remove, selection)
  * FlowList (list, manage, selection)
  * StartButton (floating, bottom-right)
- HomePage re-emits 14 signals. The MainWindow connects to those
  signals; it never reaches into the sub-widgets.

StartButton semantics:
- Disabled (grey) by default.
- Enabled (green) only when BOTH a project and a flow are selected.
- Clicking emits project_open_requested(project_id, flow_id); the
  MainWindow resolves the context and transitions to the Workspace.

ProjectTable:
- QTableWidget, not QTableView + model. A surgeon typically has
  dozens of projects, not thousands. Migration to a model is a
  separate decision, taken only if the list needs server-side
  sorting, dynamic filtering, or virtualization.
- Columns Nome, ID, Sexo, Idade, Cria├º├úo do projeto, ├Ültima
  modifica├º├úo. Sexo and Idade are reserved; the ProjectSummary
  does not carry them. They will be filled when the Patient module
  provides the data.

FlowList:
- Empty until Bloco 9 (Flow Catalog). Supports selection
  (flow_selected(str | None)) so the StartButton can react.
- Manage button emits manage_flows_requested().

Architectural boundary:
- HomePage.__init__ receives only ProjectCatalog. It does not
  receive ProjectManager. Test test_home_page_has_no_project_manager
  enforces this contract.

Tests: 820 passed. Ruff: All checks passed. Mypy: Success.

1f1f07a | 2026-10-19 23:18:17 -0300 | Jozeias Fernandes de Sousa | feat(application): add ProjectManager and ProjectAccessPolicy (piece 7.5)
ProjectManager is the single authority for the project lifecycle
(project.md ┬º4, ┬º25). It coordinates ProjectRepository, EventBus and
ProjectAccessPolicy, and publishes the lifecycle events defined in
piece 7.2.

Operations:
- create_project: persists via repository, publishes ProjectCreated.
  Defaults to DRAFT status.
- open_project: loads via repository, updates last_opened_at,
  builds ProjectContext, publishes ProjectOpened. Idempotent: a
  second open of an already-open project returns the existing
  context without publishing again.
- update_project: persists, publishes ProjectUpdated.
- close_project: publishes ProjectClosing, releases the context,
  publishes ProjectClosed. Silent no-op for non-open projects
  (closing is idempotent; a second close is not an error).
- delete_project: refuses open projects with ProjectInUse BEFORE
  touching state or publishing events. Closing implicitly would
  mix two distinct commands with different effects and could
  discard a context the user is still using.

Access policy:
- ProjectAccessPolicy (Protocol) with can_create/can_open/
  can_update/can_delete.
- Actor is a string alias for now (single-user mode); becomes a
  value object when a user model exists.
- AllowAllProjectAccessPolicy is the initial implementation.
- The policy is consulted before any mutation; denial raises
  ProjectAccessDenied and publishes nothing.

ProjectContext construction:
- Built by the Manager from the project's own metadata.
- PatientSummary is a projection: display_name and patient_id come
  from metadata; birth_date and sex are None (not carried by the
  project). Opening is self-contained; no dependency on a patient
  registry. Fresh patient data, if ever needed, is a separate query
  against a dedicated patient provider, not part of open_project.

Error hierarchy extended:
- ProjectAccessDenied (application decision; not a persistence error)
- ProjectInUse (application decision; not a persistence error)
Both derive from ProjectError directly, not from
ProjectRepositoryError: they are decisions made by the Manager
before touching persistence.

Ordering and failure semantics:
- Events are published only after a successful repository operation.
  A repository failure publishes nothing.
- ProjectClosing is published before the context is released;
  ProjectClosed is published after.

Tests: 782 passed. Ruff: All checks passed. Mypy: Success.

591fd19 | 2026-10-19 19:31:16 -0300 | Jozeias Fernandes de Sousa | feat(application): add ProjectCatalog read model (piece 7.4)
ProjectCatalog is the read-only discovery projection consumed by the
Home Page (project.md ┬º5-┬º6, startup_project_opening_workflow.md ┬º4).

- Thin wrapper over ProjectRepository. No cache, no own I/O.
  Delegates every operation to repository.list_metadata().
  Rationale: premature caching would introduce invalidation bugs
  (stale data after ProjectDeleted, cache misses during module
  switch) for no measured benefit on local SSD. If future profiling
  shows a hot path, a cache will be added in a separate piece,
  explicitly invalidated via ProjectCreated/Updated/Deleted events.
- list_projects() returns repository.list_metadata() unchanged.
- get_project_summary(project_id) returns None if not found; does
  not raise ProjectNotFound. Rationale: for discovery, "not in
  catalog" and "not persisted" are equivalent from the Home Page's
  perspective. The Project Manager (piece 7.5) is the authority for
  distinguishing them.
- search_projects(query) is case-insensitive substring over
  project_name and patient_display_name. No regex (ReDoS surface,
  unexpected user semantics). Empty/whitespace query returns all.
- count / is_empty / contains are convenience projections.
- No lifecycle methods (create/update/delete/open_project). The
  catalog is read-only by construction; tests verify the absence.
- Corrupted entries (skipped by repository.list_metadata) are
  invisible to the catalog.

Tests: 742 passed. Ruff: All checks passed. Mypy: Success.

9f8ec0c | 2026-10-19 19:20:58 -0300 | Jozeias Fernandes de Sousa | feat(infrastructure): add FilesystemProjectRepository (piece 7.3)
Implements the ProjectRepository port (piece 7.1) over a directory
tree rooted at the projects root. Same contract tests from 7.1 are
re-executed here against the real filesystem, proving the contract
is implementation-independent.

- project_serialization.py: pure Project <-> dict functions. Handles
  the persisted shape (schema_version, ISO 8601 timestamps, status
  by value). Rejects bool as schema_version (Python int subclass
  gotcha). Domain invariant violations are wrapped as
  ProjectSerializationError.
- filesystem_project_repository.py: the adapter.
  * create is atomic: writes project.json via .tmp then renames.
    On failure, rolls back the directory it created.
  * exists checks project.json, not the directory. Directories
    may exist for other persistence layers (patient_record.json,
    imaging/, models/).
  * delete removes only project.json. Other files are owned by
    other layers.
  * list_ids skips directories without project.json and non-dir
    entries.
  * list_metadata skips corrupted entries and logs them; one bad
    project does not break the Home Page.
  * All OSError/JSONDecodeError translated into the
    ProjectRepositoryError family. Callers never see raw exceptions.
- Contract tests from 7.1 re-run against tmp_path. Plus filesystem-
  specific tests: atomic create, delete-does-not-remove-directory,
  corrupted-entry resilience, path safety via ProjectPathResolver.

Note on list_ids: an earlier draft tried to filter names that are
unsafe as filesystem path components. Rejected. ProjectId (domain)
only enforces identity non-emptiness; path safety belongs to
ProjectPathResolver at the point of use. list_ids reports what
exists on disk.

Tests: 719 passed. Ruff: All checks passed. Mypy: Success.

1b39bce | 2026-10-19 19:08:35 -0300 | Jozeias Fernandes de Sousa | feat(application): add ProjectContext and lifecycle events (piece 7.2)

6c19c61 | 2026-10-19 18:56:47 -0300 | Jozeias Fernandes de Sousa | feat: close Bloco 6 (Editor Layout Tree) and open Bloco 7 (ProjectRepository)
Two pieces landed together:

Piece 6.11 ÔÇö Editor Layout Tree in AreaWidget (closes Bloco 6)
- Area gains an optional editor_layout and set_editor_layout(); the
  flat _editors list remains the authoritative membership registry.
- LayoutBuilder propagates area_spec.editor_layout to the Area.
- AreaWidget materializes the tree as nested QSplitters when set,
  falls back to the previous flat/tabs behavior when not. Backward
  compatible. This unblocks the prototype's central 2x2 layout.
- AreaWidgetError introduced for structural inconsistencies.
- Editor ABC declares tool_context(); DummyEditor switched from
  @property to method to satisfy the contract (fixes mypy).
- TopOverlay: objectName "top_overlay" (matches QFrame#top_overlay
  stylesheet) and content_layout() added.
- pyproject: ruff/mypy exclude "tools/" (internal packaging tools).

Piece 7.1 ÔÇö ProjectRepository port + contract tests (opens Bloco 7)
- ProjectRepository Protocol: create/get/update/delete/exists/
  list_metadata/list_ids. Implementations translate infrastructure
  failures into ProjectRepositoryError; no OSError/KeyError leaks.
- Error hierarchy: ProjectError ÔåÆ ProjectRepositoryError ÔåÆ
  {ProjectNotFound, ProjectAlreadyExists, ProjectCorrupted,
  ProjectStorageError}. Each carries an optional project_id.
- InMemoryProjectRepository: reference implementation used by
  contract tests and higher-layer tests; includes a
  _mark_corrupted test hook.
- 23 contract tests. The same suite will be re-run verbatim
  against FilesystemProjectRepository in piece 7.3.
- delete is deliberately non-idempotent at the contract level
  (missing ÔåÆ ProjectNotFound), so the Project Manager can
  distinguish "deleted now" from "already gone".

Tests: 643 passed. Ruff: All checks passed. Mypy: Success.

59a1f02 | 2026-10-19 10:40:09 -0300 | Jozeias Fernandes de Sousa | Created commands.md

6280857 | 2026-10-19 08:36:41 -0300 | Jozeias Fernandes de Sousa | Organizing tools

829fd75 | 2026-10-14 17:36:30 -0300 | Jozeias Fernandes de Sousa | feat(infrastructure): add path resolvers (piece 7.3)
Part A ÔÇö AppPathResolver:
- Rename ProjectPathResolver -> AppPathResolver
- Move to infrastructure/app/app_path_resolver.py
- Resolve projects_root, flows_root, cache_root from PathsConfig
- Rename ProjectRootInaccessible -> AppPathInaccessible

Part B ÔÇö ProjectPathResolver:
- New class in infrastructure/project/project_path_resolver.py
- Resolves per-project file paths from (projects_root, ProjectId)
- Rejects unsafe ProjectId values at construction (path separators,
  traversal, drive letters, control characters, leading dot)
- Rejects absolute paths and traversal in resource(), in a
  platform-independent way (Windows accepts "/..." as relative,
  POSIX does not; the resolver rejects both)
- 30 new tests

All checks green: ruff, mypy (129 files), pytest (620 passed).

25dffab | 2026-10-14 16:55:14 -0300 | Jozeias Fernandes de Sousa | Visual debug

c4445c7 | 2026-10-14 16:21:48 -0300 | Jozeias Fernandes de Sousa | test(patient): add Patient aggregate tests (piece 7.2)
- Construction with nine section value objects
- Equality and hashing by PatientId
- Women's health cross-section invariant (9 cases)
- display_name, age, summary, repr
- 28 new tests

Piece 7.2 complete: Patient domain fully covered.

591 tests passing.

All checks green: ruff, mypy, pytest.

4c2aa4a | 2026-10-14 16:19:21 -0300 | Jozeias Fernandes de Sousa | test(patient): complete Patient domain test coverage (piece 7.2)

3e5d963 | 2026-10-14 14:22:12 -0300 | Jozeias Fernandes de Sousa | Professional module documentation created

449f676 | 2026-10-14 07:58:49 -0300 | Jozeias Fernandes de Sousa | Removal of Portuguese Markdown files

83bc43e | 2026-10-14 07:55:42 -0300 | Jozeias Fernandes de Sousa | The system's appearance was created.

d634055 | 2026-10-14 00:23:22 -0300 | Jozeias Fernandes de Sousa | - Nine section value objects (identity, documents, filiation,   address, complaint, comorbidities, medications, antecedents,   habits) - Enums: PatientSex, PatientRace, BloodType, DocumentType,   PhoneKind, ComorbidityCategory - Value objects: PatientId, PhoneNumber - Patient aggregate root with cross-section invariants - PatientSummary projection - Reorganized package into enums/, value_objects/, sections/

8c38f17 | 2026-10-13 19:20:58 -0300 | Jozeias Fernandes de Sousa | feat(domain): add Project domain (piece 7.1)
- ProjectId: stable identity value object
- ProjectStatus: lifecycle enum (DRAFT, ACTIVE, ARCHIVED)
- ProjectMetadata: persistent metadata with validation and mutators
- ProjectSummary: lightweight read-only projection
- Project: aggregate root with invariant enforcement
- 41 new tests

Fixes discovered by tests:
- ProjectMetadata validates timezone-awareness BEFORE comparing
  datetimes (avoids TypeError on naive timestamps)

All checks green:
- ruff: All checks passed
- mypy: Success (103 source files)
- pytest: 420 passed

f068fb4 | 2026-10-13 18:53:13 -0300 | Jozeias Fernandes de Sousa | feat(workspace): complete Bloco 6 with Workspace facade (piece 6.10)
Piece 6.10 ÔÇö Workspace:
- Add Workspace facade tying together LayoutBuilder, LayoutRenderer,
  OverlayManager, and TopOverlay
- load_spec(spec): materialize a ModuleUISpec, render the tree,
  reposition overlays
- clear(): drop the composition without touching the TopOverlay
- areas(), area_manager(), overlay_manager(), top_overlay(): public
  read-only accessors
- resizeEvent: recompute region bounds and reposition overlays
- 18 new integration tests

Bloco 6 summary (pieces 6.1ÔÇô6.10):
- Area, AreaManager, LayoutTree, LayoutBuilder, LayoutRenderer
- Region, Bounds, LayoutTree.find_regions()
- Overlay (ABC), OverlayManager, TopOverlay
- Workspace facade
- 379 tests total, all green

All checks green:
- ruff: All checks passed
- mypy: Success (97 source files)
- pytest: 379 passed

20aeecb | 2026-10-13 16:12:32 -0300 | Jozeias Fernandes de Sousa | feat(workspace): add OverlayManager and TopOverlay (pieces 6.8, 6.9)
- OverlayManager: registry + reposition_all by Placement
- TopOverlay: Top Bar geometry (fixed height, top-anchored)
- 51 new tests, 361 passing total

All checks green: ruff, mypy, pytest.

9e21aaa | 2026-10-13 16:03:20 -0300 | Jozeias Fernandes de Sousa | feat(workspace): add Region and Overlay ABC (pieces 6.6, 6.7)
- Region + Bounds (pure domain)
- LayoutTree.find_regions()
- Overlay ABC (Qt-aware contract)
- 39 new tests, 313 passing total

All checks green: ruff, mypy, pytest.

fb0948d | 2026-10-13 15:47:12 -0300 | Jozeias Fernandes de Sousa | Mypy and Ruff fixes

eae4b7c | 2026-10-13 15:16:22 -0300 | Jozeias Fernandes de Sousa | Create internationalization

fa41887 | 2026-10-13 11:57:01 -0300 | Jozeias Fernandes de Sousa | docs: add ADR-0003 on UI widgets and editor overlays

29b39de | 2026-10-13 11:32:55 -0300 | Jozeias Fernandes de Sousa | feat(workspace): add LayoutBuilder (Block 6, Piece 4)
- Add LayoutBuilder, BuildResult, LayoutBuilderError.
- Materialize a ModuleUISpec into Areas, LayoutTree, AreaManager,
  and Editors indexed by area_id.
- Propagate context_extras per Editor with shallow copy (hybrid
  EditorContext model, ADR-0002 ┬º2.1).
- Accept shared_context as an extension point (ADR-0002 ┬º2.3); its
  contents are not yet propagated because EditorContext has no
  fields to receive them.
- Zero Qt dependency: LayoutBuilder is a pure composition step.
- Add 26 integration tests covering build shapes, depth-first
  editor order, error paths, extras isolation, and builder reuse.
- Update ADR-0001 ┬º4.1 to document that Area.add_editor rejects
  duplicate editor_ids (each Area hosts at most one Editor per id).

c927022 | 2026-10-13 09:11:10 -0300 | Jozeias Fernandes de Sousa | docs: add ADR-0002 on EditorContext and Toolbar materialization

f400389 | 2026-10-12 22:18:47 -0300 | Jozeias Fernandes de Sousa | feat(ui): Bloco 6 Pe├ºa 3 ÔÇö LayoutTree with placement-aware Area
- LayoutTree: N-ary tree of Leaf/Split organizing Areas
- LayoutTree.from_specs builds the tree from AreaSpecs
- Placement semantics documented: CENTRAL is pivot; LEFT/RIGHT/BOTTOM are satellites
- Area now carries its Placement
- AreaManager.count_by_placement and has_central helpers
- 220 tests passing; ruff and mypy clean

5a70ae0 | 2026-10-12 22:13:21 -0300 | Jozeias Fernandes de Sousa | feat(ui): Bloco 6 Pe├ºa 3 ÔÇö LayoutTree with placement-aware Area
- LayoutTree: N-ary tree of Leaf/Split organizing Areas
- LayoutTree.from_specs builds the tree from AreaSpecs
- Placement semantics documented: CENTRAL is pivot; LEFT/RIGHT/BOTTOM are satellites
- Area now carries its Placement
- AreaManager.count_by_placement and has_central helpers
- 220 tests passing; ruff and mypy clean

c1f1868 | 2026-10-12 21:48:39 -0300 | Jozeias Fernandes de Sousa | feat(ui): Bloco 6 Pe├ºa 2 ÔÇö AreaManager
- AreaManager as registry of Area instances
- Idempotent register, unregister, get, require, contains, areas
- Insertion-order preservation
- 15 unit tests; ruff and mypy clean

b6e6844 | 2026-10-12 21:45:41 -0300 | Jozeias Fernandes de Sousa | feat(ui): Bloco 6 Pe├ºa 1 ÔÇö Area
- Area as a structural container of Editors
- show/hide visibility
- add/remove/get/list Editors with duplicate-id protection
- active Editor management
- Deferred maximize note for future LayoutRenderer work
- 186 tests passing; ruff and mypy clean

efe6e3a | 2026-10-12 21:33:10 -0300 | Jozeias Fernandes de Sousa | feat(ui): complete Bloco 3 ÔÇö Editors and EditorRegistry
- DummyEditor for tests and early integration
- EditorRegistry with idempotent registration and create()
- Test fixtures: make_dummy_editor
- 168 tests passing; ruff and mypy clean

86e62b7 | 2026-10-12 21:01:42 -0300 | Jozeias Fernandes de Sousa | feat(ui): complete Bloco 2 ÔÇö Toolbar, Tools, and ThemeService
- ThemeService with immutable theme switching and icon resolution
- ToolbarSpec, ToolbarVisibilityMode, ToolbarState
- ActionItem, ToggleItem, Separator
- ToolRegistry with idempotent registration
- LogTool and ToggleTool builtin test tools
- Toolbar QWidget with orientation and theme-aware icon resolution
- Test fixtures: tool_registry, theme_service, make_toolbar_spec
- 142 tests passing; ruff and mypy clean

fcede88 | 2026-10-12 13:13:55 -0300 | Jozeias Fernandes de Sousa | Creating base of platform.

c5216b2 | 2026-10-12 12:06:01 -0300 | Jozeias Fernandes de Sousa | Creating base of platform.

ff904a2 | 2026-10-12 10:31:37 -0300 | Jozeias Fernandes de Sousa | Organizing folders

2ef4bf4 | 2026-10-12 10:26:16 -0300 | Jozeias Fernandes de Sousa | Organizing folders

f923743 | 2026-10-12 10:13:08 -0300 | Jozeias Fernandes de Sousa | Creating new folders

d90101c | 2026-10-12 09:34:58 -0300 | Jozeias Fernandes de Sousa | Corre├º├úo da Documenta├º├úo

7ad7ec2 | 2026-10-12 09:00:25 -0300 | Jozeias Fernandes de Sousa | Corre├º├úo da Documenta├º├úo

5681b31 | 2026-10-11 22:45:09 -0300 | Jozeias Fernandes de Sousa | Corre├º├úo da Documenta├º├úo

c3ca58e | 2026-10-11 22:11:48 -0300 | Jozeias Fernandes de Sousa | Corre├º├úo da Documenta├º├úo

bd113b5 | 2026-10-06 13:35:51 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo de Flows.

1dbcf97 | 2026-10-02 21:30:18 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo da homepage.

437d62a | 2026-10-02 12:39:11 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo de Project

6476792 | 2026-10-02 10:47:52 -0300 | Jozeias Fernandes de Sousa | Ajustes na Documenta├º├úo

783721f | 2026-10-02 10:24:33 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo dos Objects.

4af6dce | 2026-10-02 07:38:08 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo das Tools, Toolbars e Objects.

1ed7cbe | 2026-10-01 23:11:34 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo dos Editors

f06ad03 | 2026-10-01 00:00:35 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo da Workspace

6e8422f | 2026-09-30 23:59:09 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo da Workspace

0961455 | 2026-09-30 23:57:47 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo da Workspace

a9ded8d | 2026-09-30 23:39:21 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo da Workspace

499e3ca | 2026-09-30 23:36:32 -0300 | Jozeias Fernandes de Sousa | Documenta├º├úo da Workspace

bd1fb08 | 2026-09-30 19:15:07 -0300 | Jozeias Fernandes de Sousa | Merge remote-tracking branch 'origin/main'

e6aeee5 | 2026-09-30 19:11:26 -0300 | Jozeias Fernandes de Sousa | Merge branch 'main' of https://github.com/CranioZ/CranioZ # Please enter a commit message to explain why this merge is necessary, # especially if it merges an updated upstream into a topic branch. # # Lines starting with '#' will be ignored, and an empty message aborts # the commit.

5046290 | 2026-09-30 19:09:18 -0300 | Jozeias Fernandes de Sousa | chore: initial project setup
- Package structure under src/cranioz/
- pyproject.toml with dependencies and tooling config
- Minimal CLI entry point (cranioz.__main__:main)
- LICENSE (AGPL-3.0-or-later)
- README, .gitignore, .python-version
- docs/PRINCIPLES.md

22e0b7d | 2026-09-30 18:55:35 -0300 | CranioZ | Delete README.md

2a2abc1 | 2026-09-27 22:35:53 -0300 | CranioZ | Initial commit




---

## Before Sprint E — warm-up summary

**Phases 0–3 (partial) and Sprints A, B.**

- **Phase 0 — Foundation:** repository, `pyproject.toml`, CI,
  `ConfigurationLoader`, `AppPathResolver`, `EventBus`, boot in
  `__main__.py`.
- **Phase 1 — Domain and i18n:** Patient, Project, `EditorRegistry`,
  `LayoutBuilder`, `LayoutRenderer`, ADRs 0001–0014. Sprint B (i18n)
  migrated the shell to `TranslationService`; the
  `test_no_hardcoded_strings_in_shell_widgets.py` guard prevents
  regressions.
- **Phase 2 — Workspace:** `LayoutTree`, `AreaManager`, `Workspace`,
  `TopOverlay`, three-segment Top Bar.
- **Phase 3 — Project and Home Page:** `ProjectManager`,
  `ProjectCatalog`, `HomePage`, `MainWindow`, project lifecycle.
- **DICOM and visualization:** `DicomSeriesReader`, `DicomValidator`,
  `DicomSorter`, `Volume`, `MPRView`, `Viewport3DView`. The voxel
  ordering bug was resolved on 2026-11-06; the root cause was
  `transpose(2, 1, 0)` combined with `ravel(order="C")` in
  `VtkImageAdapter`. The contract is `int16`, `VTK_SHORT`, no
  transposition, direction matrix applied.
- **ADR-0014:** decision for Qt Widgets + modular QSS + Design Tokens
  in Python, not QML.

**Debt inherited by the next sprints:**

- `EditorContext` incomplete (Sprint C).
- `IconProvider` does not exist yet (Sprint F).
- `AreaLayoutRenderer` and `EditorStack` (Sprints G, H).
- `ProjectIndex`, coordinated deletion, async loading (Sprints I, J, K).
- 4 files with hardcoded colors listed in `_KNOWN_DEBT_FILES`.

The detail of each item lives in `implementation_plan.md` §5–§6 and in
the corresponding commits.

---

## 2026-11-09 — Sprint E: design tokens, ThemeService, ThemeCompiler

**Context.** Sprint E had to deliver the appearance foundation: tokens,
ThemeService, ThemeCompiler, SettingsService, and tests. The
specification lived in `docs/architecture/appearance/themes-and-design-tokens.md`.

**What was done.**
- `cranioz.infrastructure.settings`: SettingsService with two
  implementations (in-memory, filesystem), migrator, closed key set.
- `ui/theme/tokens.py`: 47 tokens, `ThemeMode`, `ThemeName`, validation.
- `ui/theme/service.py`: ThemeService with SYSTEM resolution via
  QStyleHints.
- `ui/theme/compiler.py`: ThemeCompiler with surface composition and
  QSS emission.
- Boot: SettingsService → ThemeService → apply → MainWindow.
- 177 new tests, 1508 passing.

**Decisions.**
- `modal_backdrop` uses a fixed `#000000`, not `background_application`.
  Reason: the backdrop must darken the interface, not tint it.
- `set_mode()` does not persist. Persistence is owned by the settings
  page, which allows a live preview before applying.
- `feedback_information` stayed at `#4A90D9` (the spec value) because
  `#0071E3` failed WCAG AA against `background_panel`.

**Debt and open items.**
- `_KNOWN_DEBT_FILES`: 4 files with hardcoded literals
  (`area_widget.py`, `workspace.py`, `workspace_spec.py`, `presets.py`).
  To be migrated in the widget migration sprint.
- `StartButton` still uses the `→` glyph; Sprint F replaces it with
  `IconProvider.icon(...)`.
- `QSlider` is not covered by the expanded QSS; the adjustment is
  deferred to the widget migration sprint.

**Next.** Sprint F — `IconProvider` + `UnicodeIconProvider` + glyph
migration.

## 2026-11-09 — Sprint F: IconProvider + UnicodeIconProvider + glyph migration

**Context.** Sprint F had to deliver the icon system: contract, Phase 2 implementation, shell migration, and contract tests. The specification lived in `docs/architecture/appearance/icons/`.

**What was done.**
- `ui/icons/`: `IconState` enum, `IconProvider` Protocol, `UnicodeIconProvider` with 66 names (60 canonical + 6 shell-specific).
- Injection: `__main__` → `MainWindow` → `Workspace` → shell widgets (`HomePage`, `TopBar` segments, `StartButton`, `FlowRow`).
- Migration: 8 files with hardcoded glyphs replaced by `provider.icon(...)`.
- Tests: 5 contract tests (`test_icon_catalog.py`, `test_icon_fallback.py`, `test_icon_theme.py`, `test_icon_widget_contract.py`, `test_icon_accessibility.py`).
- `_KNOWN_DEBT_FILES`: `workspace_spec.py` and `start_button.py` removed (glyphs are gone). `area_widget.py`, `workspace.py`, and `presets.py` remain (colors only).

**Decisions.**
- `IconProvider` lives in `ui/icons/`, not `ui/theme/icons/`. Icons are a distinct system (assets, catalog, provider), even though they depend on `ThemeService` for color.
- `EditorContext` injection deferred to Sprint C. Sprint F injects only into the shell.
- The 60-icon catalog was extended with 6 names required by the shell: `community`, `library`, `news`, `feedback`, `contribute`, `start`.

**Debt and open items.**
- `SvgIconProvider` and SVG assets remain Phase 8.
- `QImage.mirrored` and `vtkCellArray.GetData` deprecations tracked separately.
- The `test_icon_widget_contract.py` replaces the glyph-related debt from `test_no_hardcoded_appearance.py`.

**Next.** Sprint C — `EditorContext` propagation (now unblocked).

# Dev Log

**Document type:** Development log
**Status:** Active
**Scope:** Sprint-by-sprint record of what was done, what broke, and how it was resolved
**Last updated:** 2026-11-09

---

## Sprint F — IconProvider + UnicodeIconProvider + glyph migration

**Status:** ✅ Complete
**Date closed:** 2026-11-09
**Phase:** 2 (Workspace Engine & Icons)

### Objective

Deliver `IconState`, the `IconProvider` Protocol, `UnicodeIconProvider` with the closed 60-icon catalog, inject the provider into every shell widget that renders a glyph, migrate the hardcoded glyphs to `provider.icon(...)`, and add the five icon contract tests. Unblock Sprint C (`EditorContext` propagation), which depends on `icon_provider`.

### What was delivered

**Production code:**

- `src/cranioz/ui/icons/state.py` — `IconState` enum (`DEFAULT`, `HOVER`, `PRESSED`, `SELECTED`, `DISABLED`).
- `src/cranioz/ui/icons/provider.py` — `IconProvider` Protocol (`icon(name, size, state) -> QIcon`, `text_glyph(name) -> str`, `invalidate_cache() -> None`).
- `src/cranioz/ui/icons/unicode.py` — `UnicodeIconProvider` with the closed 60-icon catalog from `docs/architecture/appearance/icons/icons_and_icon_manager.md` §6.
- Injection into `MainWindow`, `Workspace`, `HomePage`, `HomeSegment`, `ModulesSegment`, `ExtrasSegment`, `Toolbar`, `StartButton`, `FlowRow`.
- Hardcoded glyphs in those widgets migrated to `provider.icon(...)`.
- `_WHITELIST` in `tests/architecture/test_no_hardcoded_strings_in_shell_widgets.py` emptied.

**Tests:**

- `test_icon_catalog.py` — count and required names.
- `test_icon_fallback.py` — unknown name and unknown text glyph.
- `test_icon_theme.py` — state → token mapping (5 parametrized cases).
- `test_icon_widget_contract.py` — AST scan of 7 widget files for hardcoded glyphs and direct `UnicodeIconProvider` imports.
- `test_icon_accessibility.py` — `HomeSegment` buttons expose accessible names.

**Test infrastructure:**

- `make_icon_provider(theme_service=None)` factory in `tests/conftest.py`.
- `icon_provider` fixture in `tests/conftest.py`.
- 17 test files updated to pass `icon_provider` to constructors:
  - `tests/conftest.py`
  - `tests/integration/ui/test_main_window.py`
  - `tests/integration/ui/test_main_window_debug_mesh.py`
  - `tests/integration/ui/test_main_window_import.py`
  - `tests/integration/ui/test_main_window_top_bar.py`
  - `tests/integration/ui/workspace/layout/test_layout_renderer.py`
  - `tests/integration/ui/workspace/workspace/test_workspace.py`
  - `tests/integration/ui/workspace/areas/test_area_widget.py`
  - `tests/unit/ui/home/test_home_page.py`
  - `tests/unit/ui/home/widgets/test_community_sidebar.py`
  - `tests/unit/ui/home/widgets/test_flow_list.py`
  - `tests/unit/ui/home/widgets/test_flow_row.py`
  - `tests/unit/ui/home/widgets/test_home_bottom_bar.py`
  - `tests/unit/ui/home/widgets/test_home_top_bar.py`
  - `tests/unit/ui/workspace/structure/test_home_segment.py`
  - `tests/unit/ui/workspace/structure/test_modules_segment.py`
  - `tests/unit/ui/toolbars/test_toolbar.py`

### What broke, and how it was resolved

**1. Sprint F changed constructors, but tests were not adapted.**

- **Symptom:** `pytest -q` produced 96 failed, 65 errors. Every failure was `TypeError: X.__init__() missing 1 required keyword-only/positional argument: 'icon_provider'`.
- **Root cause:** The Sprint F deliverable requires `icon_provider` on every widget that renders a glyph. The production constructors were updated; the tests were not.
- **Resolution:** 17 test files updated. `make_icon_provider` and `icon_provider` fixture added to `conftest.py` to centralize construction. Each test file either uses the shared fixture or builds the provider locally.

**2. `test_whitelist_entries_are_used` failed with 6 stale entries.**

- **Symptom:** The test reported `'☰'`, `'?'`, `'⚙'`, `'→'`, `'+'`, `'→'` as no longer produced by the files.
- **Root cause:** Those were the exact glyphs migrated in Sprint F. The Sprint B whitelist listed them as known debt; after migration, they became stale.
- **Resolution:** `_WHITELIST` set to `()`. The guardrail remains active against new hardcoded glyphs.

**3. `test_home_bottom_bar.py` — `RuntimeError: libshiboken: Internal C++ object (StartButton) already deleted`.**

- **Symptom:** 4 teardown/setup errors, cascading to "previous item was not torn down properly".
- **Root cause:** The fixture registered `start_button` with `qtbot.addWidget(button)`. The test then constructed `HomeBottomBar(start_button)`, which reparents the button. At teardown, Qt destroyed `HomeBottomBar` (with the child `StartButton`), and `qtbot` also tried to `close()` the already-deleted `StartButton`.
- **Resolution:** The `start_button` fixture no longer registers with `qtbot`. Only `HomeBottomBar` is registered; it owns the button.

**4. `test_toolbar_resolves_icon_name_via_theme` failed with `assert None == 'log'`.**

- **Symptom:** `button.property("icon_name")` returned `None`.
- **Root cause:** The test was written against a pre-Sprint-F plan where the icon name was stored as a dynamic property on the button. Sprint F replaced that plan with `icon_provider.icon(...)`, which returns a `QIcon`. The `Toolbar` never sets `icon_name`.
- **Resolution:** Test renamed to `test_toolbar_resolves_icon_via_icon_provider` and now asserts `button.icon().isNull() is False`. The production `Toolbar` was correct; the test was outdated. The test was previously masked because the constructor failed before reaching the assertion.

**5. `ruff` flagged `F841 Local variable 'toolbar' is assigned to but never used` in `test_unknown_tool_id_raises`.**

- **Symptom:** `ruff check` reported one unsafe fix.
- **Root cause:** The test used `try/except` style and assigned `toolbar = toolbar_factory(spec)` but never used `toolbar`.
- **Resolution:** Rewritten with `pytest.raises(KeyError, match="tool.unknown")`, which is idiomatic and eliminates the unused variable.

### Final state

| Metric | Value |
|---|---|
| Tests passing | **1527** |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Coverage | 88% |
| `ruff check` | clean |
| `ruff format --check` | clean |
| `mypy src` | clean |

Warnings: 41 (two known deprecations: `QImage.mirrored` at `mpr_viewer/view.py:216`, `vtkCellArray.GetData` at `stl.py:135`). Both tracked separately in `Next Steps.md` §7.

### Baseline change

- Before Sprint F: 1508 passing, 0 failed, 1 skipped, 88% coverage.
- After Sprint F: **1527 passing, 0 failed, 0 errors, 0 skipped, 88% coverage.**
- Net: +19 tests (the icon contract suite). The ~150 tests that were failing/erroring before the fixes returned to passing, which is why the total is not 1508 + 19 + 150 — those tests already existed and were blocked, not new.

### Documents updated

- `implementation_plan.md` — Sprint F marked ✅; Phase 2 pending work reduced; §9 Implementation Summary updated; §10 Known Issues updated.
- `Next Steps.md` — baseline corrected to 1527; Sprint F marked ✅; "Next sprint" changed from F to C; §3.2.2 rewritten as complete; §7 Known Issues updated; §8 Immediate next action rewritten for Sprint C.

### Next sprint

**Sprint C — `EditorContext` propagation.** Unblocked. Depends on Sprint E (`theme_service`, ✅) and Sprint F (`icon_provider`, ✅), both complete.

Sprint C has four parts:

1. Audit current `EditorContext` fields against the target set (9 fields).
2. Propagate missing fields.
3. Update `Workspace._create_editor` and `MainWindow._create_workspace`.
4. Add a contract test asserting every `EditorRegistry`-registered Editor receives all nine fields non-null in `initialize`.

# Dev Log

**Document type:** Development log
**Status:** Active
**Scope:** Sprint-by-sprint record of what was done, what broke, and how it was resolved
**Last updated:** 2026-11-09

---

## Sprint C — EditorContext propagation

**Status:** ✅ Complete
**Date closed:** 2026-11-09
**Phase:** 1 (Contracts, Core Domain & i18n)

### Objective

Propagate `theme_service` and `icon_provider` through `EditorContext`, and add the contract test that asserts every Editor registered in the `EditorRegistry` receives all nine context fields. Close Phase 1 formally.

### What was delivered

**Production code:**

- `src/cranioz/ui/editors/editor_context.py` — added `theme_service: ThemeService | None = None` and `icon_provider: IconProvider | None = None`. Both are optional with `None` default, consistent with the other context fields. Imports added under `if TYPE_CHECKING`.
- `src/cranioz/ui/workspace/workspace.py` (`load_spec`) — added `"theme_service": self._theme_service` and `"icon_provider": self._icon_provider` to the `shared_context` dict passed to `LayoutBuilder.build(...)`.

**Tests:**

- `tests/integration/ui/workspace/test_editor_context_propagation.py` — new contract test. Builds a real `Workspace` with `DummyEditor` registered, loads a `ModuleUISpec`, and asserts that the created `EditorContext` carries the expected instance of each propagated field.

**No changes required in:**

- `LayoutBuilder` — it constructs `EditorContext(**shared)`, so new context fields flow automatically with no closed key list.
- `TomographyEditor.initialize` / `MeshDebugEditor.initialize` — both accept the full `EditorContext` object; no per-field parameters.
- `MainWindow._create_workspace` — already passes `theme_service` and `icon_provider` to `Workspace` since Sprint E/F.

### What broke, and how it was resolved

**1. `CatalogTranslationService(catalog=None)` — `TypeError: unexpected keyword argument 'catalog'`.**

- **Symptom:** The test failed during construction with a `TypeError` from the test body, not from production.
- **Root cause:** I wrote the test assuming `CatalogTranslationService` accepts a `catalog` keyword. Its real constructor is `CatalogTranslationService(registry: TranslationCatalogRegistry, language: str = "en")`.
- **Resolution:** Replaced `CatalogTranslationService` with `IdentityTranslationService()`, which requires no registry and is explicitly documented as suitable for tests. The contract test verifies propagation, not translation.

**2. `tool_registry = ToolRegistry()` shadowed the fixture — `KeyError: 'tool_id not registered: tool.log'`.**

- **Symptom:** `load_spec` failed in `AreaWidget._build_toolbars` when materializing the `DummyEditor`'s toolbar. The toolbar references `tool.log` and `tool.toggle`, neither of which was registered.
- **Root cause:** The test received `tool_registry: ToolRegistry` as a fixture parameter (correct), but then re-assigned it inside the function body: `tool_registry = ToolRegistry()`. The fixture's registrations were discarded.
- **Resolution:** Removed the re-assignment line. The fixture's registry (which registers `tool.log` and `tool.toggle`) is now passed to `Workspace`.

**3. `ruff` SIM222 — `x is not None or True` in three asserts.**

- **Symptom:** `ruff check .` reported three unsafe fixes for `assert context.X is not None or True`.
- **Root cause:** The expression is a tautology; it passes regardless of the value. My intent was "do not fail if this field is None" — but the form made the assert meaningless.
- **Resolution:** Removed the three tautological asserts. Noted as debt in `Next Steps.md` §7:
  - `correlation_id`: not yet propagated by `Workspace` (it does not receive it in `__init__`).
  - `event_subscription`: passed as `None` in the test; a dedicated test should cover it once `EventBus` exposes a subscription helper for unit tests.
  - `domain_object_store`: not in the Sprint C target set.

**4. Windows Smart App Control blocked `vtkRenderingCore` (environmental).**

- **Symptom:** `ImportError: DLL load failed while importing vtkRenderingCore: Uma política de Controle de Aplicativo bloqueou este arquivo.`
- **Root cause:** Windows 11 Smart App Control blocks unsigned DLLs, including VTK's. The VTK wheels are not code-signed.
- **Resolution:** Smart App Control was disabled on the development machine. This is a development-environment requirement, not a code change. It must be documented in the contributor setup instructions.

### Final state

| Metric | Value |
|---|---|
| Tests passing | **1528** (1527 from Sprint F + 1 from Sprint C) |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Coverage | 88% |
| `ruff check` | clean |
| `ruff format --check` | 542 files already formatted |
| `mypy src` | 281 source files, no issues |

Warnings: 41 (the two known deprecations: `QImage.mirrored` at `mpr_viewer/view.py:216`, `vtkCellArray.GetData` at `stl.py:135`). Both tracked separately in `Next Steps.md` §7.

### Baseline change

- Before Sprint C: 1527 passing.
- After Sprint C: **1528 passing.**
- Net: +1 test (the contract test). No regressions.

### Documents updated

- `implementation_plan.md` — Phase 1 marked `✅ Implemented`; Sprint C marked `✅ Complete`; §9 Implementation Summary updated; §10 Known Issues updated; `Next sprint` changed from C to G.
- `Next Steps.md` — baseline corrected to 1528; Phase 1 marked `✅ Complete`; Sprint C marked `✅ Complete`; §7 Known Issues updated with the two new debt rows (`correlation_id`, `event_subscription`); §8 Immediate next action rewritten for Sprint G.

### Lessons learned

**Audit before implementation.** The `Next Steps.md` listed nine context fields as Sprint C deliverables, but an audit against the current codebase showed that seven already existed. Only two were missing, and both flowed automatically through `LayoutBuilder`'s `**shared` mechanism. The audit turned what looked like a multi-day sprint into a couple of hours of work — and would have been wasted effort if skipped.

**Tests reveal contract drift.** The `test_toolbar_resolves_icon_name_via_theme` failure in Sprint F and the `CatalogTranslationService(catalog=None)` failure in Sprint C were both cases of a test written against an assumed contract that production did not implement. The tests are valuable: they force the contract to be explicit. But they must be written against the real production signature, not the intended one.

**`x or True` is always a bug in a test.** If a field is optional and a test does not want to assert on it, the field should be omitted from the test, with a comment explaining why. A tautological assert adds no coverage and hides intent.

### Next sprint

**Sprint G — `AreaLayoutRenderer`.** Independent of the other open sprints. Splits `AreaWidget`'s intra-Area composition into a dedicated renderer, so that Sprint H (`EditorStack`) can build on it. No visible behavior change for the single-Editor case; the existing `test_area_widget.py`, `test_workspace.py`, and `test_main_window.py` suites must continue to pass.

### Phase impact

**Phase 1 is closed.** The contracts, core domain, i18n, and `EditorContext` propagation are complete and tested. The remaining phases in progress (2 and 3) have no dependency on Phase 1 beyond what is now stable.

This unblocks the path to Phase 4 (Scene & Visualization), which begins only after Phases 2–3 close. No further changes to the Phase 1 contract should be necessary; if a future sprint discovers a gap, it should be recorded as debt in `Next Steps.md` §7, not silently added to `EditorContext`.