# Steps Panel (`steps_panel`)

## Purpose and responsibility

The `steps_panel` is a workspace UI component that presents and controls navigation through a workflow. The same panel can serve different clinical workflows. For orthognathic surgery planning, for example, it presents one unified sequence of steps and guides the user while the workspace activates the module associated with each step.

The panel contains no clinical rules and does not determine on its own whether a step is complete. The declarative workflow definition is written in JSON. The workflow engine, implemented in Python, validates that definition, evaluates requirements, maintains case state, and asks the workspace to activate the corresponding module.

## Conceptual model

The workflow has the following hierarchy:

1. **Workflow:** an ordered sequence of work toward a clinical objective.
2. **Step:** a unit of work in the workflow, containing one or more substeps.
3. **Substep:** an action, input, configuration, or check performed by the user or system.
4. **Requirement:** a verifiable condition that determines whether a substep or step can proceed or be completed.

By default, each step is associated with one module. The workflow remains one unified list, even when each step opens a different module. The same module may appear in multiple steps. The structure allows exceptions, such as a step using more than one module, but this is not the usual case.

When the user completes a step, the Python engine checks its requirements. If completion is valid, it updates progress and asks the workspace to activate the module for the next step. The same `steps_panel` remains visible and updates the selected step and displayed states.

## Component responsibilities

### JSON workflow definition

Describes the workflow declaratively: identifier and version, name, ordered steps, the module associated with each step, substeps, instructional text and images, requirements, alternatives, dependencies, actions, and completion criteria.

### Python workflow engine

- loads and validates the JSON definition;
- checks that referenced modules, validators, and actions are known to the application;
- evaluates requirements and determines states;
- validates requests to proceed or complete a step;
- determines the next step and asks the workspace to switch modules;
- persists progress and notifies the UI of changes.

### Workspace

Organizes the work area, hosts the panel and other visual areas, and activates the module requested by the engine. The workspace does not make clinical decisions.

### `steps_panel`

Presents the sequence, active-step content, requirements, and progress. It sends user commands to the engine and reflects the state returned by it.

### Modules

Perform operations specific to their functional area and report verifiable results to the engine. Modules do not define the global workflow sequence.

## Requirements, alternatives, and completion

Each requirement is declared as mandatory or optional. Applicable mandatory requirements must be satisfied before a step can be completed. Optional requirements may remain unmet without blocking completion. Alternatives allow the same objective to be met through different methods.

For example, a facial CT may be mandatory to begin planning. An intraoral scan may be optional if the dental arches can also be segmented from the CT. If the user chooses the intraoral scan, aligning it with the CT becomes a mandatory requirement for integrating that data path.

The Python engine evaluates requirements through validators implemented and registered by the application. The JSON references these validators by known identifiers; it contains no executable code. An unknown or invalid reference must be reported as a configuration error and must never be assumed to be satisfied.

## States and transitions

The Python engine is the single authority for calculating workflow state. The panel only presents that state. The following states are defined for a step:

| State | Meaning |
| --- | --- |
| `pending` | The step has not been started. |
| `active` | The step is selected for work. |
| `blocked` | The step cannot be started or completed because a dependency or mandatory requirement is unmet. |
| `completed` | The step's completion criteria have been checked and satisfied. |

Substeps use `pending`, `active`, and `completed`; they may also use `blocked` when they depend on another substep or requirement. A step's aggregate state is derived from its substeps and requirements: it can be `completed` only when all applicable mandatory requirements are satisfied and all required substeps are complete. Optional requirements do not block completion.

Normal step transitions:

```text
pending -> active -> completed
   |         |
   +------> blocked
blocked -> pending or active, after the blocking condition is resolved
```

If evidence data is changed or removed, the engine reevaluates the requirements. A previously completed step may return to `active` or `blocked` if its criteria are no longer true; this change must be persisted and recorded in the history. Reopening a completed step for review is allowed according to workflow rules and does not erase its history.

## JSON structure and example

JSON files are the versioned source of workflow definitions. The example below shows a step that accepts two alternative paths for obtaining the dental arches. Validator and action identifiers correspond to implementations registered in the Python system.

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
      "fields": [
        {
          "id": "face_ct_file",
          "label": "Facial CT",
          "type": "file",
          "required": true,
          "accepted_formats": [".dcm", ".nii.gz"],
          "multiple": true,
          "import_action": "import_face_ct"
        },
        {
          "id": "intraoral_scan_files",
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
          "text": "A facial CT is required. For the dental arches, use intraoral scans or segmentation from the CT."
        },
        {
          "type": "image",
          "src": "assets/patient_data_guide.svg",
          "alt": "Imaging data sources used for orthognathic planning.",
          "caption": "Input data"
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
          "id": "intraoral_scans_available",
          "required": false,
          "check": "case_has_intraoral_scans"
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
          "id": "cephalometric_points_reviewed",
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

The final JSON schema is validated by the Python engine. Text fields are presented to the user; step, module, validator, and action IDs connect the declarative definition to implementations allowed by the application. The JSON sequence is the source of ordering. Explicit dependencies are validated to detect missing references or cycles.

File fields declare the selection interface, labels, required status, accepted formats, whether multiple files are allowed, and the import action. The JSON does not store the selected files or directly access filesystem paths. After the user chooses files, Python validates their formats and contents, imports them into the case, and stores persistent references to the managed objects. On resuming a case, the system restores those references and field states rather than relying on temporary session paths.

## Guidance, images, and localization

A step or substep may provide a title, description, instructions, caption, and PNG or SVG images. Text and resource paths are declarative data and cannot contain executable instructions.

Images are resources in the workflow package. The validator resolves and normalizes each relative path and confirms that the final path remains inside the package's allowed directory. It also applies an allowlist of extensions and media types, rejects absolute paths, traversal (`..`), and links that escape the package. A missing or invalid resource produces a readable validation error; the system never loads an arbitrary filesystem path.

Texts are stored directly in the workflow JSON in this version of the architecture. Future localization may use separate catalogs linked by the same stable workflow, step, and substep IDs. Localized text does not change IDs or completion logic. Catalog versioning policy will be defined when the application implements multiple languages.

## Persistence, resumption, and history

Progress is stored per clinical case, separately from the JSON files that define workflows. Closing and reopening the application must not reset the work: when a case is reopened, the engine restores the workflow and its version, active step and substep, choices, states, and references to data produced or used by modules.

Current state is kept separate from the evidence history:

- **Progress snapshot:** represents the case's current position and state for fast restoration.
- **Event/evidence history:** records relevant changes, such as a requirement becoming satisfied or invalidated, a step starting or completing, the responsible user, timestamp, and references to objects supporting the decision.

This combination keeps current progress easy to load while preserving traceability. The concrete storage technology follows the application's persistence architecture, but it must support both functions and consistent writes. Medical images and meshes are not duplicated by the panel; progress records store stable references to objects managed by modules, using persistent IDs from the data system. Temporary local paths are not valid identities for clinical objects.

Each case is associated with the definition version used to start it. A new version must not silently reinterpret in-progress cases. Incompatible changes require keeping the original definition for that case or performing an explicit, validated, and recorded migration.

## Concurrency

The system must detect when more than one user changes the same case. A progress write checks the version of the state that was read; if another user has already changed it, the system does not silently overwrite the latest update. It reloads and reevaluates requirements and states, and reports a conflict when changes cannot be merged automatically.

Step completion is always revalidated at the time it is saved. If one user completes Cephalometry while another changes the landmarks used as evidence, the engine evaluates the latest state before advancing to Osteotomies. The history identifies the author and the change that caused the state transition.

## Contract between the engine and the panel

The engine provides the panel with:

- workflow name and active step/substep;
- titles, descriptions, instructions, and guidance resources;
- ordering, associated module, and state for each step and substep;
- applicable requirements, mandatory status, result, and reason for any pending requirement;
- enabled actions and explanations for blocked actions;
- restored case progress.

The panel sends commands such as selecting a step, proceeding, or requesting completion. The engine validates each command, updates and persists state, asks the workspace to activate the corresponding module, and returns the new state to the panel. The UI does not mark steps complete locally.

## Visual characteristics and accessibility

Based on the prototypes, the panel:

- has a title bar labeled “Steps Panel” and panel controls;
- can be expanded and collapsed;
- can be moved and resized within the workspace;
- presents steps in an ordered vertical list;
- expands the active step to show substeps, instructions, and controls;
- keeps other steps in a compact format;
- provides internal scrolling when content exceeds the available space;
- communicates states clearly without relying on color alone.

The panel must be operable by keyboard, maintain visible focus and a predictable focus order, expose understandable names and states to screen readers, and use readable contrast. Step changes and validation messages must be announced without unexpected focus movement. Alternative text describes instructional images; decorative images are identified as such.

## Orthognathic planning workflow

An initial configuration may include these steps, each associated with its module:

1. Patient data.
2. Model alignment.
3. Segmentation.
4. Cephalometry.
5. Osteotomies.
6. Surgical guide.

Each step may contain multiple substeps and requirements. Once mandatory requirements are satisfied and completion is requested, the user advances to the next step and the workspace automatically activates its associated module while keeping the same `steps_panel` visible.

## Design principles

- **Unified workflow:** the panel presents one ordered sequence.
- **One step, one module by default:** exceptions are declared explicitly in JSON.
- **Separation of responsibilities:** JSON defines; Python validates and coordinates; the workspace activates modules; the panel presents and sends commands.
- **Clinical flexibility:** mandatory, optional, and alternative requirements are verifiable.
- **Resumption and traceability:** progress survives application closure and changes leave evidence.
- **Resource security:** images are loaded only from validated packages.
- **Accessibility:** information and controls work with assistive technologies and different input methods.
- **Consistency:** the state shown by the panel always comes from the workflow engine.
