# Curved MPR Editor — CranioZ

**Type:** proposed functional documentation  
**Status:** draft for clinical and technical validation  
**Version:** 0.1  
**Date:** October 6, 2026

## 1. Overview

The **Curved MPR Editor** is a proposed workspace for generating and inspecting a curved panoramic reconstruction from a tomographic volume. The user defines a reference curve over the volume; the editor resamples the data along that curve and displays the corresponding panoramic image.

The editor is part of the **Tomography Module**. It consumes an active series or volume and maintains the spatial relationship between the curve, the panoramic reconstruction, and the original volume. This proposal does not confirm that the editor or its tools have already been implemented in CranioZ.

Curved MPR is a visualization and planning tool. It does not provide a diagnosis, determine treatment, or replace interpretation by the responsible professional.

## 2. Objectives

- Define, review, and adjust a curve over a tomographic volume.
- Generate a panoramic reconstruction consistent with the volume's spatial geometry.
- Allow users to navigate between the reconstruction and the source volume while preserving spatial context.
- Expose relevant curve and resampling parameters so the result is understandable and reproducible.
- Preserve the original image and record the curve and its derivatives as case-related working data.

## 3. Functional Scope

Subject to configured and validated capabilities, the editor should allow users to:

- select the active tomographic volume;
- create a curve using user-defined control points on a view of the volume;
- display the curve overlaid on the source image;
- move, insert, or remove control points;
- generate and update the panoramic reconstruction when the curve is created or modified;
- configure or inspect parameters such as sampling spacing, reconstruction thickness, and reslice plane orientation;
- navigate the reconstruction and relate its position to the curve and volume;
- save, duplicate, rename, or remove curves, subject to permissions and history requirements;
- export the reconstruction or curve only after export formats and contracts have been defined.

The parameter list and tools should be finalized during technical design. The system should distinguish available options from values unsupported by the current volume.

## 4. User Interface Components

### 4.1 Volume View

Displays a 2D view of the volume—for example, axial, coronal, or sagittal—on which the user defines and adjusts the curve. The view should indicate orientation, slice position, scale, and the active series/volume when available.

The curve appears as a distinct, identifiable graphic overlay. Control points should remain tied to the volume's spatial coordinates, not merely to screen positions, so they remain correctly positioned when zoom, pan, or slice changes.

### 4.2 Curved MPR View

Displays the panoramic reconstruction derived from the active curve. It should identify the source curve and volume, as well as the relevant parameters used to produce the image. Navigation and adjustments should preserve a clear spatial relationship with the input data.

The view should distinguish states such as waiting for generation, processing, up to date, out of date after a curve change, and resampling failure.

### 4.3 Controls and Information

The editor should display:

- the active case, examination, series, and volume;
- the selected curve and its state;
- tools for creating and editing control points;
- active reconstruction parameters, such as spacing and thickness, when configurable;
- generate/update commands and cancellation when the operation can be safely cancelled;
- progress messages, warnings, and errors;
- save and restore-previous-version actions, according to product policy.

## 5. Curve Model

The curve represents a user-defined spatial path in the volume's coordinate system. The implementation must specify how control points are interpolated, how endpoints and closed curves are handled, and which geometric constraints are accepted. Until then, these details remain open technical decisions.

Each persisted curve should retain, at a minimum, its links to the case and source volume, control-point coordinates, coordinate system, author, date/time, and version. If interpolation or resampling parameters are used, they should be recorded with the curve or corresponding result.

### 5.1 Creation

1. The user selects the volume and reference view.
2. The user starts curve creation.
3. The user defines control points on the visible anatomy.
4. The user confirms the curve or continues adjusting it.
5. The user requests generation of the panoramic reconstruction.

The curve should only be shown as persisted after storage is confirmed. If saving fails, the interface should preserve the editable state for recovery when possible and inform the user.

### 5.2 Editing

The user can select and adjust control points, insert or remove points, and review the resulting shape. A change should mark the previous reconstruction as out of date until resampling completes. Editing does not modify the source volume and should not silently overwrite a previously saved curve.

### 5.3 Multiple Curves

If the product allows more than one curve per volume, each curve should have its own name or identifier, state, and author. Switching the active curve should be explicit. Earlier curves and their associated reconstructions remain identifiable under the project's retention rules.

## 6. Panoramic Reconstruction

The reconstruction is derived from the volume and active curve. The resampling method, plane orientation orthogonal to the curve, thickness, and intensity aggregation method must be defined by the implementation. If modes such as single-sample, average, MIP, or MinIP are supported, the active mode and its parameters should be visible.

The reconstruction should respect the available spatial geometry, including spacing, orientation, and origin. If missing or inconsistent metadata prevents reliable reconstruction, the editor should show the limitation and avoid presenting the result as valid.

Changing the curve or parameters that affect the image invalidates the previous derived result. The interface should mark the reconstruction as out of date and indicate completion only after processing succeeds.

## 7. Navigation and Spatial Synchronization

The editor views should remain clearly associated with the same source volume. When a position is selected in the panoramic reconstruction, the editor may indicate the corresponding position on the curve and in the volume view. If cross-navigation is supported, the mapping should respect the volume's coordinate system and show the location status.

Zoom, pan, or slice changes should not alter the curve's persisted spatial coordinates. Changing the active volume requires explicit confirmation or handling when the current curve is incompatible with the new volume.

## 8. Processing and Performance

Generating the reconstruction may be computationally intensive. Processing should run asynchronously, outside the UI thread, with progress updates when available. The interface should remain responsive and offer cancellation when it is safe to interrupt the operation.

The editor should coordinate with the Tomography Module's memory-monitoring and large-volume management mechanisms. Out-of-memory conditions, unsupported volumes, cancellation, or processing failures should result in an explicit, recoverable state. A failure should not corrupt the original volume or replace a valid reconstruction with an unidentified partial result.

## 9. Data, Versions, and Provenance

For each saved curve and reconstruction, retain enough references to identify:

- the source case, examination, series, and volume;
- the volume's version or stable identifier;
- the curve and its control points in volume coordinates;
- interpolation and resampling parameters used;
- reconstruction mode and intensity parameters, if applicable;
- author, date/time, state, and version;
- the relationship between previous and updated reconstructions.

A panoramic reconstruction is a derivative and does not replace the source images. Changes should create a new version or a non-destructive change record, according to CranioZ's persistence model.

## 10. States and Errors

Suggested curve/reconstruction states:

- **No Curve** — no curve is defined for the active volume;
- **Editing** — changes have not yet been confirmed;
- **Saving Curve** — persistence is in progress;
- **Ready for Reconstruction** — the curve is confirmed, but there is no up-to-date result;
- **Processing** — reconstruction is in progress;
- **Up to Date** — the result matches the current curve and parameters;
- **Out of Date** — the curve or parameters changed after the last reconstruction;
- **Failed** — the operation did not complete;
- **Cancelled** — the operation was interrupted by the user or system.

Messages should identify the affected object and step, explain the known cause, and suggest a possible action. Examples include a curve outside the volume bounds, unavailable spatial geometry, memory allocation failure, save error, or resampling failure.

## 11. Permissions and Security

Access to the editor and to create, modify, delete, export, and approve actions should follow case and project permissions. Changes must be attributable to an individually identified user. Logs and notifications should not expose more personal data than necessary.

The editor must not present a curve as clinically approved merely because it was saved or processed. Any review or approval step belongs to the Flow and the clinical rules defined by the institution.

## 12. Acceptance Criteria

1. The user can select a supported volume and create a curve in the correct spatial reference frame.
2. The curve is displayed over the volume view, and its control points remain spatially stable during zoom, pan, and slice navigation.
3. The user can adjust control points and can identify that the previous reconstruction is out of date.
4. The panoramic reconstruction is generated from the active curve and reports processing, completion, or error states.
5. The volume's spatial geometry is respected; insufficient or inconsistent data produces a warning and prevents a false success indication.
6. Processing does not block the interface and respects the module's memory and large-volume management mechanisms.
7. Curves and reconstructions remain linked to the source volume, available parameters, author, and version.
8. Changes and failures do not overwrite or corrupt the original image or a valid derivative without a record.
9. Switching the active volume explicitly handles curves that are incompatible or belong to another volume.

## 13. Open Decisions

- In which 2D views can users define the curve? Is the curve planar or can it vary in three dimensions?
- Which interpolation method will be used between control points, and what geometric constraints will apply?
- How will endpoints, closed curves, self-intersections, and curves outside the volume be handled?
- Which reconstruction parameters will be configurable: spacing, thickness, orientation, and intensity aggregation?
- Will the reconstruction support MIP, MinIP, averaging, or only single-sample resampling?
- Will navigation from the reconstruction to the volume view be bidirectional? Which position will be highlighted?
- How many curves can be maintained per volume, and how will they be organized and versioned?
- Which export formats will be needed for curves and reconstructions, in addition to volume VTI?
- What performance, memory, and volume-dimension limits are required for interactive processing?
- Which accessibility and interaction requirements apply to mouse, keyboard, and other input devices?

## 14. Limits of This Proposal

This document describes proposed functional requirements to guide discussion and implementation. Interpolation, geometry, resampling parameters, persistence, supported formats, and approval rules must be validated by the technical team and responsible clinical professionals. This documentation does not claim implemented support, regulatory compliance, or diagnostic suitability.
