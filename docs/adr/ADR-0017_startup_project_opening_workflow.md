This document consolidates the application initialization flow and the project opening flow, from boot to a Workspace ready for use. It is the operational specification that connects the architecture (project.md) to the actual implementation.

1. Application Initialization Flow (Boot)

   1. CranioZ starts
           ↓
   2. Loads configuration
           ↓
   3. Obtains the Project Root
      C:\Users\<user>\Documents\CranioZ\Projects
           ↓
   4. Project Catalog lists projects
           ↓
   5. Home Page displays the list


1.1 Detailed Breakdown
Step 1 — CranioZ starts

    main.py
       │
       ├── bootstrap application
       ├── initialize dependency container
       ├── initialize logging
       └── initialize event bus
Step 2 — Loads configuration
    
    ConfigurationLoader.load()
       │
       ├── read config/app.json
       │       ├── language
       │       ├── theme
       │       ├── recent_projects_limit
       │       └── ...
       ├── read config/paths.json
       │       ├── project_root
       │       ├── flows_root
       │       └── cache_root
       └── read config/user.json
               ├── user_id
               ├── preferences
               └── ...

Step 3 — Obtains the Project Root
The ProjectPathResolver is initialized with the root coming from configuration.


    ProjectPathResolver.initialize(project_root)
       │
       ├── default: C:\Users\<user>\Documents\CranioZ\Projects
       └── override: config/paths.json → project_root
Rules:

The Project Root is resolved once at boot and remains stable throughout the session.

If the directory does not exist, it is created with the minimal structure.

If it is not accessible, the application fails with a clear error (ProjectRootInaccessible).

Step 4 — Project Catalog lists projects

    ProjectCatalog.list_projects()
       │
       ├── read <project_root>/info.json
       │       └── if missing or corrupted:
       │             └── rebuild_index()
       │                   └── scan <project_root>/*/project.json
       │
       └── return list[ProjectSummary]
Rules:

The Catalog is a read model. It does not load clinical data.

If info.json is missing, the Catalog rebuilds the index by scanning folders.

If it is corrupted, the Catalog backs it up and rebuilds it.

Step 5 — Home Page displays the list

    HomePage
       │
       ├── receives list[ProjectSummary]
       ├── renders cards/list
       ├── enables search/filter
       └── awaits user selection
Rules:

The Home Page does not access the filesystem directly.

The Home Page does not maintain its own authoritative list.

The Home Page only displays what the Catalog provides.

2. Project Opening Flow

   User selects a project
           ↓
   Project Manager opens the project
           ↓
   Project Repository loads project.json
           ↓
   Project Manager builds the ProjectContext
           ↓
   User/Project Manager defines the Clinical Flow
           ↓
   ProjectContext + Clinical Flow → Workspace
           ↓
   Workspace initializes the Flow modules
           ↓
   Modules load the necessary data
           ↓
   Workspace ready for use

2.1 Detailed Breakdown
Step 6 — User selects a project

    HomePage
       │
       ├── user clicks project card
       ├── (optional) user selects clinical flow
       └── emit signal: project_selected(project_id)
Rules:

Selection is only an intent. Nothing is loaded yet.

The project_id is the only piece of data transferred at this step.

Step 7 — Project Manager opens the project

    ProjectManager.open_project(project_id)
       │
       ├── check access policy
       │       └── can_open(user, project_id)
       ├── check ProjectInUse
       │       └── if already open, return existing context or error
       ├── delegate to ProjectRepository.get(project_id)
       └── build ProjectContext
Rules:

Only the Project Manager initiates the opening.

Policy and concurrency checks occur before loading.

Failures return application exceptions (ProjectNotFound, ProjectAccessDenied, ProjectInUse).

Step 8 — Project Repository loads project.json

    ProjectRepository.get(project_id)
       │
       ├── resolve path: <project_root>/<uuid>/
       ├── read project.json
       │       ├── project_id
       │       ├── project_name
       │       ├── patient_id
       │       ├── status
       │       ├── clinical_procedure
       │       ├── schema_version
       │       └── timestamps
       ├── read patient_record.json
       │       ├── patient metadata
       │       ├── medical history
       │       └── logical paths
       ├── read workflow.json
       │       ├── workflow_id
       │       ├── current_step
       │       └── config
       ├── check schema_version
       │       └── if outdated: ProjectMigrationService.migrate()
       └── return Project (domain object)
Rules:

The Repository does not decide whether the project should be opened. It only loads.

Schema migrations occur here, transparently.

If any file is corrupted, it returns ProjectCorrupted.

Step 9 — Project Manager builds the ProjectContext

    
    ProjectManager.build_context(project)
       │
       ├── extract metadata (read-only)
       ├── extract patient_summary
       ├── extract project_state
       ├── resolve application services
       ├── collect object_references
       └── return ProjectContext
ProjectContext contract:


    @dataclass(frozen=True)
    class ProjectContext:
        project_id: ProjectId
        metadata: ProjectMetadata          # read-only
        patient_summary: PatientSummary
        project_state: ProjectState
        workflow_id: WorkflowId | None     # may be None until selection
        workflow_config: WorkflowConfig | None
        service_locator: ApplicationServices
        object_references: list[ObjectReference]
Rules:

The ProjectContext is an initialization snapshot, not the project itself.

It is immutable (frozen) for the Workspace.

It contains no physical paths — only logical references.

Step 10 — Defines the Clinical Flow
The flow can be defined in two ways:

A) Defined by the user on the Home Page (before opening):

    
    HomePage
       │
       ├── user selects project
       ├── user selects flow
       └── emit signal: project_selected(project_id, flow_id)
B) Resolved by the Project Manager (after opening):


    ProjectManager.open_project(project_id)
       │
       ├── ...
       ├── WorkflowResolver.resolve(project)
       │       └── determines flow based on:
       │             ├── project.clinical_procedure
       │             ├── workflow.json (if already present)
       │             └── user preferences
       └── attach workflow to context
Rules:

The Home Page does not implement workflow logic.

The WorkflowResolver is the resolution authority.

If no flow is resolved, the Workspace opens in "flow selection" mode.

Step 11 — ProjectContext + Clinical Flow → Workspace

    ProjectManager
       │
       ├── publish ProjectOpened event
       │       └── subscribers: HomePage, Catalog, ...
       │
       └── handoff to Workspace
               │
               │ ProjectContext
               │ + ClinicalFlow
               ▼
           Workspace
Rules:

The handoff is explicit. The Workspace does not fetch the context.

The ProjectOpened event is published to other subsystems.

The Workspace becomes the consumer of the context.

Step 12 — Workspace initializes the Flow modules

    Workspace.initialize(context, flow)
       │
       ├── setup layout
       ├── load flow definition
       │       └── flow.json
       ├── instantiate modules
       │       ├── ImagingModule
       │       ├── SegmentationModule
       │       ├── RegistrationModule
       │       ├── CephalometryModule
       │       └── OsteotomyModule
       ├── inject context into modules
       └── subscribe modules to event bus
Rules:

Modules are passive: they receive the context, they do not fetch it.

Each module is initialized with the ProjectContext and its WorkflowConfig.

Modules may subscribe to relevant events (WorkflowStepChanged, etc.).

Step 13 — Modules load the necessary data

    ImagingModule.initialize(context)
       │
       ├── resolve logical paths via ProjectPathResolver
       │       ├── resolve("imaging/ct")
       │       └── resolve("imaging/cbct")
       ├── load image metadata (not pixels yet)
       ├── register with workspace layout
       └── ready

    SegmentationModule.initialize(context)
       │
       ├── resolve("segmentation/maxilla")
       ├── load segmentation results (if any)
       └── ready

    OsteotomyModule.initialize(context)
       │
       ├── resolve("planning/osteotomies")
       ├── load planning data (if any)
       └── ready
Rules:

Modules load data on demand (lazy loading when possible).

Modules never build physical paths — they always use ProjectPathResolver.

Modules never persist directly — they always use application commands.

Step 14 — Workspace ready for use

    Workspace
       │
       ├── layout rendered
       ├── modules initialized
       ├── data loaded (partially)
       ├── event bus active
       └── awaiting user interaction
3. Unified Diagram

    CranioZ
      │
      ▼
    Home Page
      │
      │ ProjectSummary
      ▼
    Project Catalog
      │
      │ project_id
      ▼
    Project Manager
      │
      │ open(project_id)
      ▼
    Project Repository
      │
      │ project.json + metadata
      ▼
    Project Manager
      │
      │ ProjectContext
      │ + Clinical Flow
      ▼
    Workspace
      │
      ▼
    Modules
      │
      ├── Imaging
      ├── Segmentation
      ├── Registration
      ├── Cephalometry
      └── Osteotomy
4. Detailed Flow with Responsibilities
    
    ┌─────────────────────────────────────────────────────────────────┐
    │ BOOT                                                            │
    ├─────────────────────────────────────────────────────────────────┤
    │ main.py                                                         │
    │   ├── bootstrap application                                     │
    │   ├── ConfigurationLoader.load()                                │
    │   ├── ProjectPathResolver.initialize(project_root)              │
    │   ├── ProjectCatalog.initialize()                               │
    │   └── HomePage.show()                                           │
    └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ DISCOVERY                                                       │
    ├─────────────────────────────────────────────────────────────────┤
    │ HomePage                                                        │
    │   ├── request: ProjectCatalog.list_projects()                   │
    │   ├── receive: list[ProjectSummary]                             │
    │   ├── render: cards/list                                        │
    │   └── await: user selection                                     │
    └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ SELECTION                                                       │
    ├─────────────────────────────────────────────────────────────────┤
    │ HomePage                                                        │
    │   ├── user clicks project                                       │
    │   ├── (optional) user selects flow                              │
    │   └── emit: project_selected(project_id, flow_id?)              │
    └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ OPENING                                                         │
    ├─────────────────────────────────────────────────────────────────┤
    │ ProjectManager                                                  │
    │   ├── check access policy                                       │
    │   ├── check ProjectInUse                                        │
    │   ├── ProjectRepository.get(project_id)                         │
    │   │       ├── read project.json                                 │
    │   │       ├── read patient_record.json                          │
    │   │       ├── read workflow.json                                │
    │   │       └── check schema_version (migrate if needed)          │
    │   ├── WorkflowResolver.resolve(project)                         │
    │   ├── build ProjectContext                                      │
    │   └── publish ProjectOpened event                               │
    └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ HANDOFF                                                         │
    ├─────────────────────────────────────────────────────────────────┤
    │ ProjectManager                                                  │
    │   └── Workspace.initialize(ProjectContext, ClinicalFlow)        │
    └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ WORKSPACE INITIALIZATION                                        │
    ├─────────────────────────────────────────────────────────────────┤
    │ Workspace                                                       │
    │   ├── setup layout                                              │
    │   ├── load flow definition                                      │
    │   ├── instantiate modules                                       │
    │   ├── inject context                                            │
    │   └── subscribe to event bus                                    │
    └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ MODULE INITIALIZATION                                           │
    ├─────────────────────────────────────────────────────────────────┤
    │ Modules                                                         │
    │   ├── ImagingModule.initialize(context)                         │
    │   ├── SegmentationModule.initialize(context)                    │
    │   ├── RegistrationModule.initialize(context)                    │
    │   ├── CephalometryModule.initialize(context)                    │
    │   └── OsteotomyModule.initialize(context)                       │
    └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ READY                                                           │
    ├─────────────────────────────────────────────────────────────────┤
    │ Workspace                                                       │
    │   └── awaiting user interaction                                 │
    └─────────────────────────────────────────────────────────────────┘

5. Temporal Sequence (Mermaid)
6. Failure Points and Handling
Point	Possible Failure	Handling
Boot	ProjectRootInaccessible	Fatal error with dialog
Catalog	info.json corrupted	Rebuild index
Catalog	info.json missing	Rebuild index
Selection	No projects	Home Page shows empty state
Opening	ProjectNotFound	Notify Home Page
Opening	ProjectAccessDenied	Notify Home Page
Opening	ProjectInUse	Offer read-only mode or wait
Opening	ProjectCorrupted	Notify, offer restoration
Opening	ProjectIncompatibleSchema	Notify, block opening
Migration	Migration failure	Roll back from backup
Workspace	Module initialization failure	Isolate module, continue with others
Modules	Data loading failure	Module shows error state
7. 
7. Architectural Rules Applied
This flow respects the invariants defined in project.md:

✅ Only the Project Manager initiates the opening.

✅ The Home Page is read-only (does not write, does not persist).

✅ The Project Catalog is a read model.

✅ The Project Repository only persists/retrieves.

✅ The ProjectContext is immutable for the Workspace.

✅ The Workspace does not fetch state, it only consumes.

✅ Modules are passive.

✅ Physical paths are resolved by the ProjectPathResolver.

✅ Communication between components occurs via the Event Bus.

✅ The Clinical Flow is resolved by the WorkflowResolver.

8. Summary
The project initialization and opening flow in CranioZ follows a clear sequence:

text
BOOT       → configuration, path resolver, catalog
DISCOVERY  → catalog lists, home page displays
SELECTION  → user picks project (+ flow)
OPENING    → project manager coordinates, repository loads
CONTEXT    → project manager builds ProjectContext
HANDOFF    → project manager delivers to workspace
WORKSPACE  → workspace initializes layout and modules
MODULES    → modules load data on demand
READY      → workspace ready for use
The central principle is:

The Home Page discovers, the Project Manager coordinates, the Repository loads, the Workspace consumes, the Modules execute.

