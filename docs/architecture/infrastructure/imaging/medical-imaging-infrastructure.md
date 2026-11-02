# Medical Imaging Infrastructure

## 1. Purpose

Medical Imaging Infrastructure provides the foundation for importing, validating, representing, storing, and supplying volumetric medical images to CranioZ visualization and clinical workflows.

Its primary responsibility is to transform clinical imaging sources into a consistent internal volume representation while preserving:

- Spatial geometry and anatomical orientation.
- Voxel values and intensity calibration.
- Source traceability and provenance.
- Data integrity and ownership.
- Compatibility with the Domain, Application, Scene, and Visualization layers.

The infrastructure must distinguish technical data validity from clinical suitability. A successfully imported volume is not automatically suitable for every quantitative or diagnostic operation.

### 1.1 Design Principles

- **DICOM-first:** DICOM CT/CBCT is the primary clinical imaging source.
- **Domain independence:** Core imaging models must not depend on DICOM, VTK, ITK, or Qt.
- **Explicit geometry:** Spatial information must never be silently approximated or discarded.
- **Clinical integrity:** Intensity calibration and geometric limitations must remain explicit.
- **Single data ownership:** Avoid unnecessary voxel-buffer duplication.
- **Controlled dependencies:** Introduce libraries only when required by implemented capabilities.
- **Incremental implementation:** Build infrastructure around concrete clinical workflows.
- **Separation of concerns:** Image data, visualization state, and clinical operations must remain distinct.

---

## 2. Scope and Implementation Strategy

Medical Imaging Infrastructure is implemented incrementally within the main CranioZ Implementation Plan.

Its responsibilities span two implementation stages:

| Implementation stage | Imaging responsibilities |
|---|---|
| **Phase 4 — Scene & Visualization** | Volume representation, DICOM import foundation, geometry, Scene integration, VTK adaptation, MPR foundation, and volume visualization |
| **Phase 6A — Tomography & Segmentation** | Clinical tomography workflow, image navigation, intensity tools, segmentation, and related operations |

The imaging infrastructure must not become a separate application subsystem. It reuses the existing Domain, Application, Scene, TaskManager, and rendering architecture.

### 2.1 Initial Volume Foundation

The initial foundation provides a functional path from a DICOM CT series to a validated internal volume and its visualization.

**Included:**

1. Core volume models and spatial geometry.
2. Single-frame DICOM CT instance reading.
3. DICOM series discovery and assembly.
4. Metadata and geometry validation.
5. Intensity calibration and classification.
6. NumPy-backed voxel storage.
7. Conversion to `vtkImageData`.
8. VTI export.
9. Integration with `DomainObjectStore` and Scene.
10. Integration with the rendering pipeline and `TomographyEditor`.
11. Orthogonal MPR visualization.
12. Automated tests and import reporting.

Individual single-frame DICOM instances are assembled into a three-dimensional volume. The implementation is therefore not restricted to single-slice datasets.

### 2.2 Initial Exclusions

The following capabilities are outside the initial volume foundation:

- NIfTI, NRRD, MetaImage, and other additional volume formats.
- Compressed DICOM transfer syntaxes requiring external codecs.
- Multi-frame DICOM support.
- DICOM writing and DICOM SEG.
- Label volumes and segmentation-specific data models.
- Registration and resampling.
- Vector volumes and displacement fields.
- Advanced filtering and image-processing pipelines.
- Curved and panoramic MPR.
- Advanced quantitative imaging tools.
- ITK as a mandatory dependency.

These capabilities may be introduced when supported by a defined clinical workflow and implementation requirements.

### 2.3 Future Extensions

| Capability | Intended stage |
|---|---|
| Clinical segmentation and label volumes | Phase 6A |
| Thresholding and mask editing | Phase 6A |
| Advanced image processing | Phase 6A or later |
| Compressed DICOM decoding | As required by clinical datasets |
| Curved and panoramic MPR | Future tomography workflow |
| Volume registration | Phase 6B — Registration & Cephalometry |
| Explicit resampling and advanced spatial transforms | Phase 6A / 6B |
| Additional volume formats, including NIfTI and NRRD | When interoperability requires them |
| VTI import | Future interoperability extension |
| DICOM SEG import/export | Future clinical interoperability |
| DICOM writing | Future interoperability requirements |
| Vector volumes and displacement fields | Specialized workflows |
| Sample Data catalog | Future application-level capability |

The architecture should permit these extensions without requiring speculative abstractions in the initial implementation.

---

## 3. Architecture and Responsibilities

Medical imaging follows the existing CranioZ architectural boundaries.

### 3.1 Domain

The Domain defines imaging concepts independently of file formats and visualization frameworks.

Proposed organization:

```text
domain/
├── imaging/
│   ├── volume.py
│   ├── volume_geometry.py
│   ├── image_metadata.py
│   └── volume_provenance.py
│
└── scene/
    ├── transform.py
    └── domain_object_store.py
```

Responsibilities:

- Define the `Volume` model.
- Define physical geometry and voxel indexing.
- Store relevant image metadata.
- Represent intensity calibration.
- Preserve source provenance.
- Enforce domain-level invariants.

The Domain may use NumPy for numerical buffer representation, but must not depend on pydicom, VTK, ITK, or Qt.

The existing spatial transformation contracts remain authoritative. Imaging must reuse or extend them rather than introduce competing transform models.

### 3.2 Infrastructure

Infrastructure handles external formats, decoding, conversion, and export.

Proposed organization:

```text
infrastructure/
├── imaging/
│   ├── dicom/
│   │   └── dicom_series_reader.py
│   │
│   └── vti/
│       └── vti_writer.py
│
├── visualization/
│   └── vtk_image_adapter.py
│
└── rendering/
    └── vtk_actor_factory.py
```

Responsibilities:

- Read and decode DICOM instances.
- Discover and assemble compatible image series.
- Validate external imaging data.
- Convert internal volumes into VTK representations.
- Export derived volumes to VTI.
- Report unsupported formats and inconsistencies.

`vtk_image_adapter.py` converts a `Volume` into `vtkImageData`.

`vtk_actor_factory.py` creates the corresponding visual representation using the image adapter. It must not duplicate image conversion logic.

The existing volume handling in `vtk_actor_factory.py` should be completed through this consolidated pipeline. Do not introduce overlapping VTK adapters.

### 3.3 Application

The Application layer coordinates imaging operations through existing commands and services.

Relevant components include:

- `CommandBus` and `CommandExecutor`.
- `CommandStack`.
- `TaskManager`.
- `DomainObjectStore`.
- Scene and rendering integration.

DICOM import must use the existing command architecture.

The current `ImportDicomSeriesCommand` is appropriate while the operation is explicitly DICOM-specific. A source-independent `ImportVolumeCommand` should only be introduced when multiple import formats require a common application-level operation.

Long-running import and processing operations must use the existing `TaskManager`. Do not create imaging-specific task infrastructure.

### 3.4 Visualization

The visualization layer consumes the internal volume representation through adapters.

It must not:

- Read DICOM files directly.
- Own the clinical voxel data.
- Implement clinical image-processing rules.
- Modify anatomical geometry to satisfy display preferences.

The `TomographyEditor` resolves volumes through the existing `DomainObjectStore` and provides the necessary representations to its views.

Visualization state, such as Window/Level, LUT selection, slice position, and display orientation, must remain separate from the underlying clinical volume.

### 3.5 Clinical Modules

Clinical modules implement workflow-specific operations using the imaging infrastructure.

Examples include:

- Segmentation and mask editing.
- Threshold-based selection.
- ROI-based analysis.
- Curved and panoramic reconstruction.
- Quantitative image analysis.
- Registration and surgical planning.

These capabilities must consume the shared volume representation rather than introduce independent image-data ownership.

---

## 4. Core Data Model

### 4.1 Volume

`Volume` represents a three-dimensional medical image.

Conceptual attributes:

| Attribute | Description |
|---|---|
| `data` | NumPy-backed voxel buffer |
| `geometry` | Physical spatial geometry |
| `metadata` | Relevant image metadata |
| `intensity_scale` | Intensity calibration classification |
| `provenance` | Source and processing history |

The voxel buffer is logically owned by `Volume`.

The model must expose a consistent interface for accessing voxel data and spatial information. Mutations must follow controlled domain operations rather than uncontrolled modifications through visualization adapters.

### 4.2 VolumeGeometry

`VolumeGeometry` defines the relationship between voxel coordinates and physical coordinates.

Attributes:

- `origin`: physical position of the first voxel, in millimeters.
- `spacing`: voxel spacing `(sx, sy, sz)`, in millimeters.
- `direction`: spatial orientation matrix.
- `dimensions`: volume dimensions `(nx, ny, nz)`.

The internal physical coordinate convention is **RAS**.

DICOM uses **LPS**. Conversion between these conventions must occur explicitly at the infrastructure boundary.

The spatial mapping is:

\[
P_{world} = O + D \cdot (S \odot P_{index})
\]

Where:

- \(P_{world}\) is the physical coordinate.
- \(O\) is the physical origin.
- \(D\) is the direction matrix.
- \(S\) is the spacing vector.
- \(P_{index}\) is the voxel index.
- \(\odot\) represents component-wise multiplication.

### 4.3 Array and Index Conventions

CranioZ uses the following conventions:

| Concept | Convention |
|---|---|
| NumPy array order | `[z, y, x]` |
| Voxel index | `(i, j, k)` = `(x, y, z)` |
| Physical coordinates | RAS |
| DICOM coordinates | LPS |
| Distance unit | Millimeters |
| Spacing order | `(sx, sy, sz)` |
| Origin | Physical location of the first voxel |

Adapters must handle any ordering or coordinate conversion required by external libraries.

These conventions must remain consistent across import, geometry calculations, sampling, rendering, and export.

### 4.4 ImageMetadata

`ImageMetadata` contains relevant imaging information, such as:

- Modality.
- Study and series identifiers.
- Study and series descriptions, when available.
- Acquisition date, when available.
- Manufacturer and equipment information.
- Relevant acquisition parameters.
- Image dimensions.
- Pixel representation.
- Rescale slope and intercept.
- Transfer syntax.
- Other metadata required for validation and provenance.

Only metadata necessary for the application should be exposed to the Domain. DICOM-specific structures must remain in Infrastructure.

Patient-identifying information must be handled according to the project's privacy and data-protection requirements. It must not be unnecessarily exposed in UI summaries, telemetry, or logs.

### 4.5 IntensityScale

The volume must explicitly identify its intensity calibration.

Initial classifications:

| Value | Meaning |
|---|---|
| `HU` | Values calibrated to Hounsfield Units |
| `UNCALIBRATED` | Values are available but not quantitatively calibrated |
| `UNKNOWN` | Calibration cannot be established |

For conventional CT, the reader must apply the appropriate rescale slope and intercept when required.

Hounsfield Units must only be assigned when calibration is established.

CBCT values must not automatically be treated as HU. Their quantitative reliability depends on acquisition and reconstruction characteristics.

Infrastructure reports the intensity scale. Clinical modules determine which operations and thresholds are appropriate.

HU-based presets and segmentation thresholds must not be silently applied to uncalibrated CBCT data.

### 4.6 VolumeProvenance

`VolumeProvenance` preserves the origin and processing history of a volume.

It should include:

- Source references.
- Source identifiers.
- Source file or series hashes.
- Import timestamp.
- Import parameters.
- Geometry assumptions or corrections.
- Intensity calibration information.
- Processing operations, when applicable.
- Import validation outcome.

Provenance must allow the application to distinguish original clinical data from derived representations.

### 4.7 Volume Presentation Metadata

Information required to identify and list volumes must be available to the application without making presentation state part of the voxel data.

Relevant information includes:

- Display name or series description.
- Modality.
- Acquisition date, when available.
- Dimensions.
- Voxel spacing.
- Slice count.
- Intensity scale.
- Source storage mode.
- Validation status.

Project-specific classifications, such as preoperative or postoperative, must remain project-level metadata or workflow associations. They must not be treated as intrinsic properties of the image volume.

Load state and view-specific presentation state belong to the Application or UI layer.

---

## 5. DICOM Import Pipeline

### 5.1 Initial Reader

The initial reader uses:

- `pydicom` for DICOM parsing.
- NumPy for pixel arrays and numerical operations.
- VTK for spatial representation and visualization.

The initial reader supports single-frame CT DICOM instances with uncompressed transfer syntaxes.

Compressed transfer syntaxes must be detected explicitly. If the required decoder is unavailable, import must fail with a clear diagnostic.

Compressed pixel data must never be interpreted as ordinary uncompressed pixel values.

Additional codecs, potentially through GDCM or ITK, may be introduced later when actual datasets require them.

### 5.2 Import Workflow

The import workflow should follow these stages:

1. **Source selection:** The user selects a folder or files containing DICOM data.
2. **Discovery:** Candidate DICOM instances are identified.
3. **Series grouping:** Instances are grouped by `SeriesInstanceUID`.
4. **Classification:** Image instances are distinguished from scouts, dose reports, and other non-image objects.
5. **Series selection:** The user selects the intended image series.
6. **Metadata preview:** Relevant series information is presented.
7. **Identity validation:** Patient identity is compared with the active project patient record, when applicable.
8. **Data and geometry validation:** The selected series is checked for compatibility and spatial integrity.
9. **Storage selection:** The user chooses External Reference or Managed Copy.
10. **Import execution:** The series is decoded and assembled into a `Volume`.
11. **Import report:** The user receives the validation outcome and relevant warnings.
12. **Scene integration:** A successfully imported volume becomes available through the existing object and Scene architecture.

The discovery and preview stages should avoid loading complete pixel arrays unnecessarily.

### 5.3 Series Assembly

The reader must:

1. Identify candidate DICOM instances.
2. Validate modality and compatibility.
3. Read image orientation and position.
4. Determine slice ordering from physical positions.
5. Validate slice spacing.
6. Decode pixel data.
7. Apply the appropriate intensity rescaling.
8. Assemble the volume in `[z, y, x]` order.
9. Construct `VolumeGeometry`.
10. Generate metadata and provenance.
11. Produce an import validation report.

Files must not be ordered solely by filename or `InstanceNumber`.

Physical slice positions must determine spatial ordering.

### 5.4 Metadata Preview

The import interface should expose only the metadata needed to identify and evaluate candidate series.

Useful fields include:

- Study Description.
- Series Description.
- Modality.
- Manufacturer and model, when available.
- Acquisition Date, when available.
- KVP, when available.
- Slice Thickness.
- Pixel Spacing.
- Number of instances.
- Image dimensions.

Metadata preview must not expose every DICOM attribute by default.

Patient-identifying information must be minimized and displayed only when required for identity validation or clinical workflow purposes.

### 5.5 Patient Identity Validation

When importing into an existing patient project, the application should compare available DICOM identity fields with the project's patient record.

Relevant fields may include:

- Patient ID.
- Birth Date.
- Sex.

A mismatch must generate a clear warning and require explicit user confirmation before proceeding.

Any confirmation or accepted discrepancy must be recorded in the import provenance.

Patient-identifying information must not be written to ordinary application logs or telemetry.

### 5.6 Geometry Validation

The reader must validate:

- Image dimensions.
- Pixel spacing.
- Image orientation.
- Image position.
- Slice ordering.
- Slice spacing.
- Direction matrix consistency.
- Coordinate conversion.
- Presence of required metadata.

Geometry must not be silently invented or corrected.

#### Irregular Slice Spacing

The physical distance between consecutive slices must be evaluated.

A regular volume must not be constructed by collapsing inconsistent slice intervals into a single `spacing_z`.

If irregularity exceeds the defined tolerance, standard volume import must be rejected and reported.

Future implementations may provide explicit resampling to a regular grid.

#### Gantry Tilt

A slice stack with lateral displacement between consecutive slices may contain gantry tilt.

A direction matrix constrained to orthonormal axes cannot represent this shear.

The initial implementation must detect and report unsupported tilt. It must not silently discard the displacement or force the dataset into an orthogonal grid.

Future implementations may support a more general affine geometry or explicit resampling.

#### Handedness and Coordinate Conversion

The implementation must distinguish between:

- Coordinate-basis conversion, such as LPS to RAS.
- Actual reflection of the image data.

LPS-to-RAS conversion involves a basis transformation with a reflection component. This must not be confused with invalid anatomical geometry.

The final spatial orientation must be validated independently. A determinant of `-1` in a coordinate-conversion matrix is not, by itself, evidence of invalid source geometry.

Display preferences such as left-right flipping must never rewrite the underlying anatomical geometry.

### 5.7 Imperfect DICOM Data

Missing or inconsistent metadata must be reported.

The reader must not silently invent origin, orientation, or spacing.

If a recovery strategy is supported, it must:

1. Explain the missing or inconsistent information.
2. Identify the assumptions required.
3. Require explicit user confirmation when clinically relevant.
4. Record the assumptions in `VolumeProvenance`.
5. Mark the resulting geometry as assumed or lower-confidence.

The initial implementation should reject datasets with missing essential geometry unless an explicitly defined and confirmed recovery path exists.

Multi-frame and non-standard DICOM datasets are outside the initial scope and must be reported as unsupported.

### 5.8 Import Validation Report

Every import operation must produce a user-readable report.

The report should contain:

- Number of files detected.
- Number of valid image instances.
- Number of excluded or unsupported instances.
- Modality.
- Transfer syntax.
- Image dimensions.
- Voxel spacing.
- Orientation.
- Intensity scale.
- Validation issues.
- Assumptions or corrections.
- Final import outcome.

The report must distinguish technical import success from unresolved clinical limitations.

Relevant validation information must also be associated with the volume provenance.

Validation severity and behavior are defined in Section 6.

---

## 6. Validation and Import Reporting

Validation is mandatory before a volume enters the application.

Validation results use three severity levels:

| Severity | Meaning | Behavior |
|---|---|---|
| Error | Data cannot be safely interpreted or imported | Blocks import |
| Warning | Potential inconsistency or assumption | Requires review or confirmation when relevant |
| Information | Relevant diagnostic information | Does not block import |

### 6.1 Validation Responsibilities

Validation covers different aspects of the imaging data:

- **Format validation:** Supported modality, transfer syntax, and image encoding.
- **Structural validation:** Required attributes, dimensions, and compatible instances.
- **Geometric validation:** Orientation, position, spacing, and spatial consistency.
- **Intensity validation:** Pixel representation and calibration.
- **Clinical limitations:** Conditions that may restrict quantitative or workflow-specific use.

Technical validation must not claim diagnostic validity.

### 6.2 Validation State

The application should retain the validation outcome associated with each imported volume.

The volume list may present a concise validation indicator, while the complete report remains accessible for review.

A warning must not be silently converted into a successful unrestricted state.

---

## 7. Scene Integration and Data Ownership

A successfully validated volume becomes available through the existing `DomainObjectStore` and Scene architecture.

The intended flow is:

```text
DICOM Files
    |
    v
DicomSeriesReader
    |
    v
Volume + VolumeGeometry
    |
    v
Validation
    |
    v
ImportDicomSeriesCommand
    |
    v
DomainObjectStore
    |
    v
Scene Membership
    |
    v
RenderingAdapter
    |
    v
VTK Representation
    |
    v
TomographyEditor / MPR Views
```

The exact command and object registration mechanisms must follow the existing contracts and ADRs.

### 7.1 Ownership

- `Volume` owns the voxel buffer.
- `DomainObjectStore` owns the lifecycle of stored domain objects.
- Scene manages membership and associations, not voxel-buffer duplication.
- Rendering components own their visual representations, not the clinical data.
- Editors consume representations and must release them when disposed.

The project must not maintain multiple independent copies of the same voxel buffer without an explicit requirement.

Closing a project must release its associated references after dependent consumers have been disposed.

The existing `DomainObjectStore`, ADR-0008, `objects.md`, and `datatypes.md` remain the authoritative references for object ownership and lifecycle behavior.

---

## 8. Memory Management and Library Interoperability

Volume data may be large. Buffer ownership and lifetime must therefore be explicit.

### 8.1 NumPy and VTK

The NumPy array is the logical backing storage for the volume.

When VTK uses the NumPy buffer without copying:

- The adapter must retain a strong reference to the NumPy array.
- The VTK representation must not outlive the buffer it references.
- The adapter must not independently free the buffer.
- Mutations must follow the defined volume access policy.
- Explicit copies must be made when required by ownership or compatibility constraints.

The implementation must verify the actual lifetime behavior of the selected VTK conversion mechanism rather than assuming that a wrapper automatically retains the source array.

### 8.2 ITK Interoperability

ITK or SimpleITK may be introduced for advanced medical image processing.

Conversions between NumPy, VTK, and ITK may involve copies. Zero-copy behavior must never be assumed without verification.

The application must document ownership and lifetime at every conversion boundary.

### 8.3 Dependency Strategy

| Library | Role |
|---|---|
| NumPy | Numerical buffer representation |
| pydicom | DICOM parsing and uncompressed pixel decoding |
| VTK | Image representation, MPR, volume rendering, VTI |
| ITK / SimpleITK | Optional future processing and decoding |
| Qt / PySide6 | User interface integration |

ITK must not be a mandatory dependency in the initial implementation.

Dependencies should be added to `pyproject.toml` according to the capabilities actually implemented.

---

## 9. Project Storage and Data Integrity

CranioZ must distinguish original clinical sources from derived imaging representations.

### 9.1 Source Storage Modes

During import, the user chooses how the original DICOM source will be handled.

**External Reference**

- The project references the original DICOM location.
- Source files are not copied.
- Storage duplication is avoided.
- Project portability depends on the original location remaining accessible.

**Managed Copy**

- DICOM files are copied into the project.
- The project becomes more self-contained.
- Storage requirements increase.
- The user must explicitly authorize copying identifiable clinical data.

The application must not silently copy patient-identifiable data into project storage.

Deleting a project may delete project-managed files, but must never delete externally referenced source files.

### 9.2 Derived Data

Derived imaging representations must be distinguishable from original clinical sources.

VTI export is supported as an interoperability and derived-data operation. The original DICOM series remains the canonical clinical source.

A derived VTI file must retain a provenance link to its source volume.

Suggested project organization:

```text
Project/
├── project.json
├── patient_record.json
├── scene.json
│
└── imaging/
    ├── sources/
    │   └── [managed DICOM data]
    │
    └── volumes/
        └── [derived VTI files]
```

The actual directory structure must follow the project's persistence contracts.

### 9.3 Data Integrity

The application should preserve:

- Source identifiers and hashes, when available.
- Import parameters and validation outcome.
- Volume geometry.
- Intensity calibration.
- Relationships between original and derived data.

Missing external references must be reported. The application must not silently replace missing source data with an unrelated file.

---

## 10. VTI Export

VTI export provides a VTK-compatible representation of a volume.

The export implementation must preserve, where supported:

- Voxel values.
- Dimensions.
- Spacing.
- Origin.
- Direction matrix.
- Scalar data type.
- Relevant scalar metadata.

The export process must not silently alter image geometry or intensity values.

A successful export should be verified through read-back tests.

VTI is a derived representation and must not replace the original DICOM source as the canonical clinical record.

VTI import is not part of the initial scope. It may be introduced later as a separate reader with explicit geometry, metadata, and compatibility validation.

---

## 11. Visualization Integration

The visualization layer presents volume data through the existing Editor and rendering architecture.

It must consume `Volume` through the VTK image adapter and must not create a second source of clinical image data.

### 11.1 MPR Architecture

The `TomographyEditor` provides the primary interface for volumetric image navigation.

The MPR implementation should use a controlled VTK reslicing pipeline based on `vtkImageReslice`, rather than making `vtkResliceImageViewer` the architectural dependency.

The reslicing pipeline must receive the volume's spatial geometry and preserve the relationship between voxel indices and physical coordinates.

This choice does not eliminate the need to manage Qt/VTK rendering contexts and OpenGL lifecycle correctly.

### 11.2 Orthogonal MPR

The initial MPR workflow provides:

- Axial view.
- Coronal view.
- Sagittal view.
- Correct physical orientation.
- Consistent anatomical coordinates.
- Slice position control.
- Slice scrolling.
- Synchronized crosshair.
- Physical coordinate display.
- Synchronized or independent navigation, according to the view state.

All views must derive their positions from the same volume geometry.

Display orientation labels must reflect the actual physical orientation. They must not be inferred from array order alone.

### 11.3 Slice Navigation and Multiple Slices

The MPR interface should support user-controlled slice navigation.

Relevant controls include:

- Current slice position.
- Slice scrolling.
- Slice interval or distance.
- Number of simultaneously displayed slices.
- Synchronized navigation between orthogonal views.
- Independent navigation when required.

The number of displayed slices and the distance between them are presentation parameters. They must not modify the source volume or its geometry.

The implementation must avoid unnecessary resampling or duplication of the full volume when displaying multiple slices.

### 11.4 Oblique MPR

Oblique MPR requires arbitrary reslicing planes defined in physical coordinates.

The implementation must preserve the relationship between the reslicing plane and the original volume geometry.

Oblique MPR may be introduced when the required interaction and clinical workflows are implemented. It must not be approximated by rotating the underlying anatomical data.

### 11.5 Image Display Pipeline

Image display parameters must remain separate from the volume's voxel values.

The display pipeline may include:

- Window/Level.
- Lookup Tables (LUT).
- Inversion.
- Brightness and contrast adjustments.
- Display presets.

These operations modify presentation, not the original clinical data.

Window/Level must be applied consistently across relevant MPR views when synchronization is enabled.

Presets must respect the volume's intensity classification. HU-based presets must not be assumed valid for uncalibrated CBCT data.

Custom preset editing and serialization may be implemented separately from the initial display pipeline.

### 11.6 Intensity Sampling

The visualization layer should support sampling voxel intensity at a selected physical position.

The operation must:

1. Receive a physical coordinate in RAS.
2. Convert it to the corresponding voxel index using `VolumeGeometry`.
3. Check whether the position is inside the volume.
4. Retrieve the stored voxel value.
5. Apply the established intensity calibration when appropriate.
6. Present the value with its correct unit or calibration status.

The displayed result must distinguish stored values from calibrated values.

This behavior supports an intensity probe without requiring a separate clinical image-data model.

### 11.7 Volume Rendering

Volume rendering must use the existing rendering architecture.

The intended path is:

```text
Volume
  |
  v
vtk_image_adapter.py
  |
  v
vtkImageData
  |
  v
Volume Rendering Representation
  |
  v
Viewport3DView
```

The implementation may use VTK volume mappers and transfer functions.

The volume representation must remain a visualization of the original `Volume`, not an independent clinical dataset.

Rendering presets and transfer functions are presentation parameters. They must not modify voxel values.

### 11.8 ROI and Segmentation Distinction

The architecture must distinguish three concepts:

| Concept | Responsibility |
|---|---|
| Display ROI | View-only region or measurement overlay |
| Processing ROI | Region of interest supplied to a processing operation |
| Segmentation Mask | Derived volumetric data identifying selected voxels |

A display ROI must not implicitly create or modify a segmentation mask.

Processing ROI must be passed explicitly to the operation that consumes it.

Segmentation masks require their own data model and lifecycle. They are part of the clinical segmentation workflow, not the initial `Volume` model.

### 11.9 Curved and Panoramic MPR

Curved MPR and panoramic reconstruction are future tomography capabilities.

They require:

- A user-defined or imported trajectory.
- A local orientation along the trajectory.
- Sampling of the original volume along the curved path.
- A defined output geometry and display convention.

These operations must generate derived views without modifying the original volume.

Their implementation should be driven by concrete dental and orthognathic workflows rather than introduced as generic infrastructure prematurely.

---

## 12. Tomography Editor and Volume List

The `TomographyEditor` coordinates volume presentation and navigation.

It must resolve volumes through the existing `DomainObjectStore` and provide the necessary data to its views.

### 12.1 Volume List

The volume list should provide enough information to identify and distinguish imported datasets.

Suggested fields:

- Display name or Series Description.
- Modality.
- Acquisition date, when available.
- Dimensions.
- Voxel spacing.
- Slice count.
- Source storage mode.
- Validation status.
- Load state.

Preoperative and postoperative classifications belong to the project or clinical workflow, not to the intrinsic `Volume` model.

The list must distinguish imported datasets from derived representations when both are present.

### 12.2 Editor Responsibilities

The `TomographyEditor` is responsible for:

- Resolving available volumes.
- Selecting the active volume.
- Providing volume representations to MPR and 3D views.
- Coordinating relevant navigation state.
- Exposing display controls.
- Disposing of view resources when the Editor is closed.

It must not own the canonical voxel buffer or implement DICOM parsing.

---

## 13. Testing Strategy

Testing must cover technical correctness, spatial integrity, data ownership, and visualization behavior.

### 13.1 Domain Tests

- Volume construction.
- Geometry validation.
- Voxel indexing conventions.
- Index-to-world conversion.
- World-to-index conversion.
- Intensity scale classification.
- Provenance consistency.
- Volume metadata validation.

### 13.2 DICOM Tests

- Valid single-frame CT series.
- Correct physical slice ordering.
- Correct rescale slope and intercept.
- LPS-to-RAS conversion.
- Missing essential metadata.
- Inconsistent dimensions.
- Irregular slice spacing.
- Gantry tilt detection.
- Unsupported transfer syntaxes.
- Unsupported multi-frame datasets.
- Duplicate or incompatible instances.
- Series grouping and classification.

### 13.3 Adapter and Export Tests

- NumPy-to-VTK conversion.
- Buffer lifetime.
- Geometry preservation.
- VTI write and read-back.
- Data integrity after round-trip conversion.
- Scalar type and intensity preservation.

### 13.4 Visualization Tests

- Orthogonal MPR orientation.
- Physical slice positioning.
- Crosshair synchronization.
- Slice navigation.
- Multiple-slice display parameters.
- Window/Level behavior.
- Intensity sampling.
- Volume rendering integration.
- Resource disposal.

Tests must distinguish headless data and geometry tests from tests that require a valid Qt/VTK rendering context.

### 13.5 Integration Tests

- DICOM import command.
- Import validation report.
- DomainObjectStore registration.
- Scene membership.
- Rendering adapter integration.
- TomographyEditor volume loading.
- MPR visualization.
- Project close and resource release.
- External Reference and Managed Copy behavior.

Tests should use public, simulated, or appropriately anonymized datasets. No identifiable clinical data should be committed to the repository.

---

## 14. Completion Criteria

### 14.1 Phase 4 — Imaging Foundation

The imaging foundation is complete when:

1. A DICOM CT series can be selected and discovered.
2. Supported instances can be decoded and assembled.
3. Geometry and intensity calibration are validated.
4. Unsupported or inconsistent data produce explicit diagnostics.
5. A valid `Volume` is constructed with explicit geometry and provenance.
6. The volume is registered through the existing DomainObjectStore and Scene architecture.
7. VTK representations are created through the established adapter path.
8. Orthogonal MPR displays the correct physical orientation.
9. VTI export preserves voxel values and spatial geometry.
10. Project closure releases dependent resources correctly.
11. Automated tests cover critical data, geometry, and ownership paths.
12. No production code relies on unimplemented placeholders in the delivered workflow.

### 14.2 Phase 6A — Tomography and Segmentation

The clinical tomography workflow requires additional completion criteria:

- Volume selection and identification.
- MPR navigation and synchronized coordinates.
- Configurable slice spacing and multiple-slice display.
- Window/Level and LUT controls.
- Intensity sampling.
- Volume rendering.
- Segmentation and mask lifecycle.
- ROI behavior consistent with the distinctions in Section 11.8.
- Clinical workflow integration and validation.

These capabilities must not be considered complete merely because the underlying volume infrastructure exists.

---

## 15. Architectural Constraints

The following constraints apply to all future extensions:

- Do not introduce imaging-specific task infrastructure; use the existing `TaskManager`.
- Do not duplicate `DomainObjectStore`, Scene, or rendering responsibilities.
- Do not introduce competing spatial transform models.
- Do not place DICOM or VTK dependencies in the Domain.
- Do not treat CBCT intensities as HU without established calibration.
- Do not silently approximate irregular or incomplete geometry.
- Do not modify anatomical geometry to implement display-only orientation preferences.
- Do not duplicate voxel buffers without an explicit reason.
- Do not treat VTI as the canonical clinical source.
- Do not mix visualization parameters with clinical voxel data.
- Do not conflate display ROI, processing ROI, and segmentation masks.
- Do not introduce advanced imaging abstractions before a concrete workflow requires them.
- Do not include mesh formats such as STL and OBJ in medical-volume infrastructure. They belong to geometry and mesh infrastructure.
- Do not expose unnecessary patient-identifying information through logs, telemetry, or UI summaries.

The architecture should remain extensible, but extensibility must not become a reason to implement speculative abstractions prematurely.

---

## 16. Future Architecture Direction

As clinical workflows mature, Medical Imaging Infrastructure may evolve to support:

- Additional volume formats and import adapters.
- Compressed DICOM transfer syntaxes.
- Multi-frame DICOM.
- Explicit resampling and more general spatial geometries.
- Registration and spatial transformations.
- Segmentation and label volumes.
- DICOM SEG interoperability.
- Advanced image processing.
- Curved and panoramic MPR.
- Quantitative imaging operations.
- Additional derived-data formats and interoperability workflows.

Each extension must define its data model, ownership, validation requirements, and integration with existing Application and Scene contracts before implementation.

The infrastructure must remain a shared foundation for clinical modules, not a repository of module-specific tools.