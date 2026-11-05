# Next Steps

**Document type:** Action plan  
**Status:** Active  
**Scope:** Immediate next work items after the VTK pipeline validation  
**Last updated:** 2026-11-05

---

## Context

The VTK rendering pipeline was validated using the STL path (`read_stl` → `Mesh` → `mesh_to_polydata` → `Viewport3DView.set_mesh`). A mesh renders correctly in the `Viewport3DView` when the application is launched with `CRANIOZ_DEBUG_MESH=1`.

This confirms:
- The renderer, camera, `vtkPolyDataMapper`, `vtkActor`, and OpenGL context are healthy.
- The DICOM visualization bug is isolated to the `vtkImageData` path (`VtkImageAdapter`, `vtkImageReslice`, transfer functions).
- The Geometry Infrastructure initial subset (Mesh, STL import/export, VTK adapter, `MeshDebugEditor`) is functional.

The next steps are organized by priority. Item 1 is the only explicit blocker for declaring Phase 4 complete.

---

## Priority 1 — Resolve the DICOM Visualization Bug

**Status:** Open, paused, scope narrowed.  
**Reference:** `docs/known_issues/dicom_visualization_bug.md` §7.  
**Blocker for:** Phase 4 completion.

### Why first

It is the only explicit blocker. The scope is now precise: the bug lives in the `vtkImageData` path, not the renderer. Trial-and-error is avoided by following the systematic plan below.

### Systematic plan

1. **Reproduce with a synthetic volume.**
   - Build a `Volume` with a synthetic shape (sphere or cube) and known geometry (identity direction, known spacing, known origin).
   - Render it in both `MPRView` (axial, coronal, sagittal) and `Viewport3DView`.
   - Observe whether the bug reproduces with a volume that has *no* DICOM-derived direction matrix.
   - If the synthetic volume renders correctly, the bug is in the DICOM reader's geometry (direction matrix, LPS→RAS conversion, or slice ordering).
   - If the synthetic volume fails, the bug is in the `VtkImageAdapter`, `vtkImageReslice` axes, or transfer functions.

2. **Log the geometry.**
   - In `VtkImageAdapter.to_vtk()`, log `volume.geometry.direction`, `origin`, `spacing`, `dimensions`, and the resulting `vtkImageData` parameters (`GetDirectionMatrix`, `GetExtent`, `GetOrigin`, `GetSpacing`).
   - Compare with what `vtkImageReslice` and `vtkSmartVolumeMapper` expect.

3. **Test the direction matrix hypotheses.**
   - **Hypothesis A:** The direction matrix is non-identity (e.g., a 90° rotation) and `vtkImageReslice` uses fixed axes (identity), causing misalignment.
     - Fix: either reorient the volume to identity in the adapter, or set reslice axes from the direction matrix.
   - **Hypothesis B:** The `np.ravel(order='F')` in `VtkImageAdapter` produces the wrong scalar ordering for VTK.
     - Fix: test with `order='C'` and `ascontiguousarray`.
   - **Hypothesis C:** `SetDirectionMatrix` is being ignored or misinterpreted by VTK.
     - Fix: test with and without `SetDirectionMatrix`, and with an explicit reorient via `vtkImageReslice` in the adapter.

4. **Test with the legacy `DicomEngine` approach.**
   - The legacy code (which worked) did not use a direction matrix and built the `vtkImageData` with `ravel(order='C')`.
   - Replicate that approach in the current `VtkImageAdapter` as a control.

5. **Document the resolution and add regression tests.**
   - Once resolved, add a test with a synthetic `Volume` that verifies the `vtkImageData` produced by the adapter has the expected geometry.
   - Add a visual regression test if feasible (headless VTK, no OpenGL context required for geometry checks).

---

## Priority 2 — Complete the RenderingAdapter and Scene Persistence

**Status:** Pending.  
**Reference:** ADR-0008, ADR-0009, `scene.md` §26, §51.

### Work items

1. **`RenderingAdapter`.**
   - Observe Scene events (`ObjectAdded`, `ObjectRemoved`, `ObjectTransformed`).
   - Update VTK actors and mappers accordingly.
   - Ensure the adapter is the sole bridge between the Scene and VTK.

2. **Scene serialization.**
   - Implement `scene_to_dict` / `scene_from_dict` per ADR-0009.
   - Persist membership, hierarchy, transforms, and relationships.
   - Validate round-trip with reference scenes.

3. **Filesystem-backed Scene persistence.**
   - `FilesystemSceneProvider` (or equivalent) loading from `scene.json`.
   - Integration with the project open/close lifecycle.

4. **Complete integration.**
   - Commands → Scene → imported objects.
   - Ensure `ImportDicomSeriesCommand` registers the `Volume` in both `DomainObjectStore` and `Scene`.

---

## Priority 3 — Complete the Medical Imaging Infrastructure

**Status:** Pending.  
**Reference:** `medical-imaging-infrastructure.md`.

### Work items

1. **Storage modes.**
   - External Reference (project references source DICOM).
   - Managed Copy (DICOM copied into the project).
   - User confirmation before copying identifiable data.
   - Project deletion never removes external source data.

2. **VTI export.**
   - `VtiWriter` as a derived representation.
   - Round-trip validation (geometry, dimensions, spacing, origin, scalar values).
   - Provenance link to the source volume.

3. **Import UI.**
   - File/directory selection.
   - Series discovery and grouping.
   - Metadata preview with minimized PHI exposure.
   - Patient identity validation and explicit mismatch confirmation.
   - Storage mode selection.
   - Validation report presentation.
   - TaskManager progress, cancellation, and error reporting.

4. **Patient identity and PHI.**
   - Compare DICOM identity fields with the project's patient record.
   - Explicit confirmation on mismatch; record in provenance.
   - No PHI in logs or telemetry.

---

## Priority 4 — Complete Module Loading

**Status:** Pending.  
**Reference:** `modules.md` v10, ADR-0001, ADR-0002.

### Work items

1. **Dependency resolution in `InMemoryModuleLoader`.**
   - Topological sort, cycle detection, version constraints.
2. **Resolve module `entry_point` declarations.**
   - Import the entry point, instantiate the Module, validate the interface.
3. **Register contributions.**
   - Tools, Editors, Services, Flows.
4. **Populate `BUILTIN_MANIFESTS`.**
   - Each built-in module's manifest.
5. **Share the application EventBus.**
   - Ensure all `ModuleContext`s reference the same `EventBus` instance.
6. **First functional built-in module.**
   - Validate activation, deactivation, failure, and unload.

---

## Priority 5 — Close Phase 2 Pending Items (Parallel)

**Status:** Pending.  
**Reference:** ADR-0013 §2.5, §2.6, §10.9, §10.10, §10.11.

These items are not blockers for Phase 4 but are tracked as known debt. They can be done in parallel or after Priority 1.

### Work items

1. **Editor Layout Tree configurable per Area (ADR-0013 §7.3).**
   - `AreaWidget` currently uses a fixed horizontal `QSplitter` for multiple Editors.
   - Honor `Area.set_editor_layout(EditorLayoutSpec)`.

2. **Editor Stack (ADR-0013 §2.5).**
   - Small switcher in the Editor's corner for stacking multiple Editors in the same Leaf.
   - Not a `QTabWidget`.

3. **`IconManager` and `ThemeService` semantic colors.**
   - Replace Unicode glyphs in the Top Bar.
   - Implement `ThemeService.color("active")`, etc. (ADR-0003).

---

## Recommended Sequence

1. **Priority 1** — DICOM visualization bug (blocker).
2. **Priority 2** — RenderingAdapter and Scene persistence (unblocks Editor workflows).
3. **Priority 3** — Medical Imaging Infrastructure (unblocks the clinical tomography workflow in Phase 6A).
4. **Priority 4** — Module loading (unblocks Phase 5 and Phase 6).
5. **Priority 5** — Phase 2 pending items (polish, parallelizable).

---

## Definition of Done for Priority 1

- A synthetic `Volume` (sphere or cube) renders correctly in `MPRView` and `Viewport3DView`.
- A real DICOM series renders correctly in `MPRView` and `Viewport3DView`.
- The `VtkImageAdapter` geometry is verified against the `Volume.geometry` with a regression test.
- The fix is documented in `docs/known_issues/dicom_visualization_bug.md`, marked as resolved, and linked from `implementation.md` §10.5.