# Clinical Workflows

## 1. Purpose

A **Clinical Workflow** is a versioned, declarative sequence that guides a user through a clinical task by coordinating steps, requirements, and application modules. It expresses how work is organized without duplicating the clinical functionality implemented by modules.

This document describes workflow concepts, configuration, execution, state, and persistence. The `steps_panel` document describes the reusable UI component that presents a workflow. The Workspace document describes how that panel is hosted as a shared Overlay.

## 2. Core concepts

### 2.1 Workflow

A workflow has a stable identifier, a display name, a version, and an ordered list of steps. JSON is the source format for workflow definitions. A workflow may be provided by the platform, a module, or a plugin, subject to validation and compatibility rules.

### 2.2 Step

A step is a meaningful unit of work in the workflow. Each step has a stable ID and is associated with one module by default. The same module may be used in multiple steps. A step may contain substeps, guidance, input fields, requirements, dependencies, and completion criteria.

The step list is defined once by the workflow and remains unified as the user moves between modules. A step is not itself a module, view, or workspace Area.

### 2.3 Substep

A substep is a more focused action or check within a step, such as orienting a model, importing a data source, reviewing landmarks, or confirming a result. Substeps may have their own instructions, fields, requirements, and state.

### 2.4 Requirement

A requirement is a verifiable condition used to determine whether an action, substep, or step may proceed or be completed. Requirements are mandatory or optional. A mandatory requirement blocks completion while it remains unmet; an optional requirement does not.

Alternative requirements allow more than one valid path to the same outcome. For example, dental arches may be obtained from aligned intraoral scans or segmented from a facial CT. If intraoral scans are selected, their alignment to the CT becomes a requirement for that path.

## 3. Relationship to modules and the Workspace

The workflow engine and module activation belong to the Application layer. The Workspace is not the workflow controller and does not know clinical step semantics.

The usual transition is:

1. The workflow engine determines the active step and its associated module.
2. The Application layer loads or activates that module.
3. The Application layer provides the module's `ModuleUISpec` to the Workspace.
4. The Workspace materializes the specification and preserves its shared `steps_panel` Overlay.
5. The panel displays the updated workflow state and sends user actions back to the application.

When a step is completed, the workflow engine evaluates its requirements. If the completion criteria are met, it persists the transition and asks the application to activate the module for the next step. The Workspace only materializes the resulting module UI specification; it does not decide which module comes next.

By default, one step references one module. This keeps the workflow straightforward to configure and navigate. A module can appear in several steps. A future workflow that genuinely needs one step to coordinate several modules must declare that explicitly and be validated; it must not be inferred from a step's title or position.

## 4. Responsibilities

### JSON workflow definition

The JSON definition declares stable identifiers, order, modules, user-facing content, file-input descriptions, requirement references, dependencies, actions, and completion criteria. It contains data only; it does not contain Python snippets, algorithms, or executable callbacks.

### Python workflow engine

The Python engine:

- loads and validates workflow definitions;
- checks references to modules, validators, and actions against registries/contracts;
- evaluates applicable requirements using application and module results;
- computes workflow, step, and substep states;
- validates user requests to proceed or complete a step;
- requests module activation through the Application layer;
- persists progress and publishes state changes to the UI.

Unknown module, requirement, or action IDs are configuration errors. They must not be silently ignored or treated as satisfied.

### Modules

Modules perform their clinical or technical operations and report verifiable results to the Application layer. They do not own the global step sequence. Module results and data objects are referenced by stable IDs rather than by temporary UI state or local paths.

### `steps_panel`

The shared panel presents the flow, its active step, instructions, requirements, and progress. It sends commands to the application and displays the returned state. It does not evaluate clinical criteria or mark a step complete locally. Visual behavior and accessibility requirements are specified in `steps_panel.md`.

## 5. JSON definition

Workflow definitions are stored as versioned JSON files. The JSON sequence is the source of step order. A definition may include:

- workflow ID, name, version, and description;
- ordered steps and their module IDs;
- optional substeps;
- titles, descriptions, instructional text, captions, and image references;
- file-input declarations;
- requirement IDs and mandatory/optional status;
- alternative satisfaction paths;
- dependencies between steps;
- contextual action IDs and completion criteria.

The Python engine validates each definition against a schema before execution. It checks unique IDs, valid module and action references, dependency references, dependency cycles, supported field types, and resource references.

### 5.1 Example

The following example shows a mandatory CT, optional intraoral scans, and two valid ways to meet the mandatory dental-arches requirement.

```json
{
  "id": "orthognathic_planning",
  "name": "Orthognathic Planning",
  "version": 1,
  "steps": [
    {
      "id": "patient_data",
      "title": "Patient Data",
      "module": "patient_data_module",
      "description": "Select the data to be used for planning.",
      "file_inputs": [
        {
          "id": "face_ct",
          "label": "Facial CT",
          "type": "file",
          "required": true,
          "accepted_formats": [".dcm", ".nii.gz"],
          "multiple": true,
          "import_action": "import_face_ct"
        },
        {
          "id": "intraoral_scans",
          "label": "Intraoral scans",
          "type": "file",
          "required": false,
          "accepted_formats": [".stl", ".ply", ".obj"],
          "multiple": true,
          "import_action": "import_intraoral_scans"
        }
      ],
      "guidance": [
        {
          "type": "text",
          "text": "A facial CT is required. Dental arches may come from aligned intraoral scans or segmentation of the CT."
        },
        {
          "type": "image",
          "src": "assets/patient_data_guide.svg",
          "alt": "The data sources used for planning.",
          "caption": "Planning inputs"
        }
      ],
      "requirements": [
        {
          "id": "face_ct_available",
          "required": true,
          "check": "case_has_face_ct"
        },
        {
          "id": "dental_arches_available",
          "required": true,
          "satisfy_any": [
            "intraoral_scans_aligned",
            "dental_arches_segmented_from_ct"
          ]
        },
        {
          "id": "selected_scans_aligned",
          "required": true,
          "when": "intraoral_scans_selected",
          "check": "intraoral_scans_aligned"
        }
      ],
      "completion": {
        "all_required_satisfied": true
      }
    },
    {
      "id": "cephalometry",
      "title": "Cephalometry",
      "module": "cephalometry_module",
      "depends_on": ["patient_data"],
      "description": "Acquire and review cephalometric landmarks.",
      "requirements": [
        {
          "id": "landmarks_reviewed",
          "required": true,
          "check": "cephalometry_points_reviewed"
        }
      ],
      "completion": {
        "all_required_satisfied": true
      }
    },
    {
      "id": "osteotomy",
      "title": "Osteotomies",
      "module": "osteotomy_module",
      "depends_on": ["cephalometry"],
      "description": "Plan and review the osteotomies.",
      "requirements": [
        {
          "id": "osteotomy_plan_reviewed",
          "required": true,
          "check": "osteotomy_plan_reviewed"
        }
      ],
      "completion": {
        "all_required_satisfied": true
      }
    }
  ]
}
```

The identifiers in `check`, `when`, and `import_action` refer to implementations registered by the Python application. The JSON describes which checks and actions apply; the application code executes them.

File-input declarations describe a selection field and accepted formats. They do not store file contents or authorize arbitrary filesystem access. After user selection, the application validates and imports the files, then records stable references to the managed objects. Temporary session paths are not persisted as object identities.

## 6. Workflow state and transitions

The workflow engine is the authority for state. The UI presents the state it receives and cannot independently mark a step complete.

### 6.1 Step and substep states

| State | Meaning |
| --- | --- |
| `pending` | Not started. |
| `active` | Currently selected for work. |
| `blocked` | Cannot proceed or complete because a dependency or mandatory requirement is unmet. |
| `completed` | Required substeps and applicable mandatory requirements have been verified. |

Substeps use the same state model. A step is `completed` only when its completion criteria are satisfied. Optional requirements can remain unmet. Normally one step is active at a time; later steps may be blocked by unmet dependencies.

### 6.2 State transitions

```text
pending -> active -> completed
   |         |
   +------> blocked
blocked -> pending or active, when its blocking condition is resolved
completed -> active or blocked, if supporting data changes and criteria no longer hold
```

The engine reevaluates affected requirements when data or module results change. If a completed step becomes invalid, the engine updates the current state and records the reason; it does not erase the prior completion event. A user may return to an earlier step for review according to the workflow's navigation rules.

## 7. Persistence, resumption, and versioning

Workflow definition and per-case progress are separate:

- The versioned JSON file defines the workflow and is not mutated to store user progress.
- Persisted project or case state records the active workflow ID and definition version, active step/substep, requirement status, user choices, and stable references to relevant module objects.

Closing and reopening a case restores its workflow progress, so the user can continue from the saved state. Large CTs, scans, and meshes are managed by the data/persistence architecture; workflow state stores references to them rather than duplicating them.

The persistence model keeps a current progress snapshot for restoration and an event/evidence history for relevant changes, such as starting or completing a step, satisfying or invalidating a requirement, the actor, timestamp, and references supporting the result. Writes must preserve consistency between state and recorded evidence.

Each case remains associated with the workflow definition version under which it began. A new definition version must not silently change the interpretation of an in-progress case. An incompatible change requires retaining the original definition or performing an explicit, validated, and recorded migration.

When multiple users may edit the same case, writes check the version of the state read. Concurrent changes must not be silently overwritten. Before recording step completion, the engine reevaluates requirements against the latest state and reports conflicts that cannot be merged safely.

## 8. Content and resource validation

Workflow JSON may provide user-facing titles, descriptions, instructions, labels, captions, and references to PNG or SVG images. The content is declarative and is never executed as code.

Images belong to a known workflow resource package. Before loading a reference, the validator normalizes the relative path, confirms the resolved file remains inside the allowed package directory, checks its extension and media type against an allowlist, and rejects absolute paths, traversal (`..`), and links escaping the package. Missing or invalid resources produce clear validation errors.

Texts are stored directly in the workflow JSON in the current architecture. If multiple languages are introduced, translation catalogs may refer to stable workflow, step, and substep IDs without changing workflow logic. Catalog versioning is a separate localization decision.

## 9. Workflow execution lifecycle

1. The application loads the workflow JSON and validates its schema and registered references.
2. The engine loads or initializes progress for the project/case and resolves the workflow definition version.
3. The engine determines the active step and asks the application to activate its associated module.
4. The module provides results through application contracts; the Workspace materializes its `ModuleUISpec`.
5. The shared `steps_panel` displays the active flow, current step, guidance, inputs, requirements, and progress.
6. User actions from the panel or module are sent to the engine as application commands.
7. The engine reevaluates requirements, validates requested transitions, persists state and evidence, and publishes updated presentation state.
8. When the step is complete, the engine selects the next eligible step and requests activation of its module.
9. When the project/case is reopened, the engine restores the saved workflow progress and resumes at the appropriate step.

## 10. Orthognathic planning example

An initial orthognathic planning workflow may use this ordered sequence:

1. Patient data — `patient_data_module`
2. Model alignment — `registration_module`
3. Segmentation — `segmentation_module`
4. Cephalometry — `cephalometry_module`
5. Osteotomies — `osteotomy_module`
6. Surgical guide — `surgical_guide_module`

The sequence is illustrative; the JSON definition is authoritative. Each step may contain multiple substeps. For example, Cephalometry may include choosing a reference method, orienting the head, acquiring or reviewing landmarks, and confirming the result. After mandatory criteria are satisfied and the user completes the step, the application activates the next step's module while the same `steps_panel` remains visible.

## 11. Validation and failure handling

Workflow definitions are validated before use. At minimum, validation checks:

- schema and version support;
- unique workflow, step, substep, field, and requirement IDs;
- known module, validator, and action references;
- valid dependency references and absence of dependency cycles;
- supported input field types and file-format declarations;
- resource paths constrained to the workflow package;
- valid completion rules and alternatives.

If a definition is invalid, the application reports the affected workflow and configuration issue clearly and does not execute an incomplete or ambiguous definition. If an individual optional guidance resource is missing, the application reports it and may continue when the resource is not required for safe execution.

## 12. Design principles

- **Declarative configuration:** JSON describes workflow structure and content; Python implements execution.
- **Unified sequence:** a workflow owns one ordered list of steps across module changes.
- **Module composition:** steps normally map to one module; modules do not own the global sequence.
- **Verifiable completion:** mandatory criteria are checked by registered application logic.
- **Flexible paths:** alternatives are explicit and optional requirements do not block valid paths.
- **Resumable cases:** workflow progress is persisted separately from its definition.
- **Traceability:** state changes retain evidence and stable references.
- **Workspace independence:** the Workspace hosts the shared panel and materializes module UI specs without interpreting workflow semantics.
- **Safe resources:** file inputs and image references are validated by the application.
