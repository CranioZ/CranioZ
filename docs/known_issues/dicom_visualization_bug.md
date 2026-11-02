# Known Issue — DICOM Visualization Bug

**Status:** Open (paused)
**Date:** 2026-11-02
**Priority:** High (blocks visual debug of CT/CBCT)
**Affected phase:** Phase 4 — Scene & Visualization

---

## 1. Symptom

After importing a DICOM series (CT/CBCT), the Views hosted by the
`TomographyEditor` do not render the volume correctly:

- **MPR (Axial, Coronal, Sagittal):** display uniform gray rectangles
  (or tilted polygons) instead of anatomical slices. No contrast is
  visible.
- **3D (`Viewport3DView`):** displays only the `vtkOutlineFilter`
  bounding box, or a distorted/streaked volume. The internal
  structures are not rendered.

The data pipeline works: the `DicomSeriesReader` reads the slices,
the `ImportDicomSeriesHandler` registers the `Volume` in the
`DomainObjectStore` and the `Scene`, and the `TomographyEditor`
resolves the `Volume` and passes it to the Views.

## 2. Context

- **Imported volume:** dims=(400, 400, 248), spacing=(0.2, 0.2, 0.2),
  `intensity_scale=UNCALIBRATED` (range -6114 to 16383).
- **Log:** `CT volume has range (-6114, 16383) outside the expected HU
  range; treating as uncalibrated`.
- **Environment:** Windows, PySide6, VTK 9+.

## 3. Diagnosis

The problem is in the **orientation of the volume** and in the
**configuration of the visualization parameters**:

1. **Direction matrix:** the `VolumeGeometry` carries a direction
   matrix (RAS), but the `VtkImageAdapter` was applying it via
   `SetDirectionMatrix` on the `vtkImageData`. The `vtkImageReslice`
   in the MPR, in turn, used fixed axes (identity), causing
   misalignment between the slice plane and the volume.
2. **Reorientation:** an attempt to use `vtkImageReslice` inside the
   `VtkImageAdapter` to reorient the volume to identity failed. The
   `SetOutputExtent` was incorrect, causing the volume to be clipped
   (empty or partial slices).
3. **Window/Level (MPR):** the W/L was being computed from the full
   range (`min`/`max`), mapping almost the entire volume to a single
   gray tone. An attempt with percentiles (1% and 99%) also did not
   resolve the issue, because the volume was not being sampled
   correctly.
4. **Transfer function (3D):** the `"cbct"` preset did not cover the
   real range of the volume. An attempt to dynamically adapt the
   transfer function to the real range also did not resolve the issue,
   because the 3D volume still appeared distorted (streaked).

## 4. Attempts Made

| Attempt | Files Changed | Result |
|---|---|---|
| W/L from `volume.scalar_range` (min/max) | `MPRView` | MPR showed a uniform gray block |
| W/L from percentiles (1% and 99%) | `MPRView` | MPR still showed a gray block (no contrast) |
| `"cbct"` preset with earlier opacity | `presets.py` | 3D still showed outline only |
| `"cbct"` preset with earlier opacity + dynamic adaptation | `Viewport3DView` | 3D showed a streaked/distorted volume |
| Reorientation via `vtkImageReslice` in `VtkImageAdapter` | `VtkImageAdapter` | Black screen (empty volume) |
| Reorientation via `vtkImageReslice` with correct `SetOutputExtent` | `VtkImageAdapter` | Clipped volume (partial slices) |
| Removal of reorientation; only `SetDirectionMatrix` | `VtkImageAdapter` | MPR with tilted polygons; 3D with partial volume |
| Removal of `SetDirectionMatrix` (assume axial) | `VtkImageAdapter` | MPR with gray rectangles; 3D with streaked volume |
| Reslice axes based on direction matrix | `MPRView` | MPR with tilted/clipped slices |

## 5. Hypotheses for the Next Iteration

1. **Verify the real direction matrix of the volume.** The DICOM
   direction matrix may not be the identity (e.g., a 90° rotation
   around an axis). Print the matrix to the log and compare with what
   VTK expects.
2. **Investigate the MPR `vtkImageReslice`.** The reslice axes (fixed
   or based on the matrix) may be incorrect. Test with a synthetic
   volume (sphere) to isolate the problem.
3. **Investigate the `vtkSmartVolumeMapper`.** The 3D volume may be
   rendering, but with the wrong transfer function. Test with a
   `vtkFixedPointVolumeRayCastMapper` or adjust the
   `ScalarOpacityUnitDistance`.
4. **Compare with the legacy `DicomEngine`.** The legacy code (which
   worked) did not use a direction matrix and built the `vtkImageData`
   with `ravel(order='C')` and `np.ascontiguousarray`. Replicate that
   approach in the current `VtkImageAdapter`.
5. **Verify that `Volume.data` is being correctly converted.** The
   `Volume` stores data in `(nz, ny, nx)` and the `VtkImageAdapter`
   uses `ravel(order='F')`. Test with `order='C'` and
   `ascontiguousarray`.
6. **Test with a synthetic volume.** Create a `Volume` with a sphere
   or cube and verify that the MPR and 3D render it correctly. This
   isolates the problem from the DICOM data.

## 6. Files Involved

- `src/cranioz/infrastructure/visualization/vtk_image_adapter.py`
- `src/cranioz/ui/editors/mpr_viewer/view.py`
- `src/cranioz/ui/editors/viewport_3d/view.py`
- `src/cranioz/ui/editors/viewport_3d/presets.py`
- `src/cranioz/infrastructure/imaging/dicom/dicom_series_reader.py`
- `src/cranioz/domain/imaging/volume.py`
- `src/cranioz/domain/imaging/volume_geometry.py`

## 7. Next Steps (when resuming)

1. Reproduce the bug with a synthetic volume (sphere) to isolate the
   problem.
2. Print the direction matrix and the `vtkImageData` parameters to the
   log.
3. Test the legacy `DicomEngine` approach (no direction matrix,
   `ravel(order='C')`).
4. Investigate `vtkImageReslice` and `vtkSmartVolumeMapper` with a
   synthetic volume.
5. Document the final solution and add regression tests.

## 8. Decision

The correction work is **paused** to avoid further trial-and-error.
The project will resume with a systematic approach (see §7). This
issue must be resolved before Phase 4 can be considered complete.