## Purpose

The Project subsystem defines how CranioZ creates, identifies, discovers, opens, maintains, persists, and closes clinical projects.

A **Project** is the persistent clinical container associated with a patient and one or more clinical workflows. It provides the boundary within which patient-related data, imaging, models, planning data, workflow state, metadata, and other clinical artifacts are organized.

Project management is deliberately separated from the **Home Page** and the **Workspace**.

The central architectural rule is:

> **The Project Manager is the single application-level authority for the lifecycle of a project. The Home Page discovers and selects projects. The Project Repository persists them. The Workspace operates on the selected project without owning its lifecycle.**

This separation prevents multiple components from independently creating, modifying, deleting, or persisting projects.

---

# 1. Architectural Model

CranioZ separates project management into distinct responsibilities:

| Component | Responsibility | Project lifecycle mutation |
|---|---|---:|
| **Project Manager** | Owns project lifecycle and coordinates project-level operations | Yes |
| **Project Catalog** | Provides a read-only discovery projection of available projects | No |
| **Project Repository** | Loads and persists project state | No* |
| **Project Storage** | Provides physical storage infrastructure | No |
| **Project Access Policy** | Evaluates authorization for project operations | No |
| **Project Context** | Represents the active runtime context supplied to the Workspace | No |
| **Home Page** | Discovers, displays, and selects projects | No |
| **Workspace** | Executes clinical workflows using an opened project | No |

\\* The repository performs persistence operations requested by the Project Manager. It is not the authority that decides whether a project should be created, updated, opened, or deleted.

The architecture is intentionally asymmetric:

                             Project Management
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                  Project Manager        Project Catalog
                         │                     │
              ┌──────────┼──────────┐          │
              │          │          │          ▼
              ▼          ▼          ▼      Home Page
          Repository   Access     Events
              │        Policy
              ▼
         Persistent
           Project
    
    Project Manager
           │
           │ ProjectContext + ClinicalWorkflow
           ▼
       Workspace
           │
           ▼
     Clinical Flows / Modules


The diagram describes architectural responsibilities, not necessarily concrete classes.

2. Project and Patient

A Patient and a Project are different concepts.

A Patient is a domain entity representing the person associated with clinical data.

A Project is the persistent clinical/application container used by CranioZ to organize the patient's data and the clinical planning performed for that case.

Conceptually:

Patient
   │
   │ referenced by
   ▼
Project
   │
   ├── Patient-related data
   ├── Imaging
   ├── Models
   ├── Analysis
   ├── Planning
   ├── Workflow state
   └── Project metadata

The Patient is therefore not simply an anonymous set of fields embedded in the Project.

However, CranioZ does not define an independent PatientManager in this architecture.

The project lifecycle remains the responsibility of the Project Manager:

A Patient is a domain entity referenced by a Project. Within CranioZ, patient-related project data is managed through the Project Management boundary; there is no separate Patient lifecycle manager.

This prevents competing ownership between PatientManager and ProjectManager.

3. Project Identity

Every Project has a stable unique identifier.

The identifier must remain independent of:

patient name;
project display name;
filesystem path;
current workflow;
workspace instance;
UI representation.

A project may expose metadata such as:

Project ID
Project Name
Patient Summary
Created At
Updated At
Last Opened At
Project Status
Schema Version
Current Workflow

The exact metadata model belongs to the Project domain documentation.

The identifier is the canonical reference used by application services, repositories, events, and runtime contexts.

4. Project Lifecycle Ownership

The Project Manager is the single application-level authority for project lifecycle operations.

It is responsible for coordinating:

project creation;
project initialization;
project opening;
project metadata updates;
project closure;
project deletion;
project archival/restoration when supported;
project validation;
project access checks;
project persistence;
project lifecycle events.

The Project Manager may delegate individual operations to repositories, storage services, access policies, or other application services, but those components do not become independent lifecycle authorities.

The following operations must pass through the Project Manager:

Create Project
Open Project
Update Project
Close Project
Delete Project
Archive Project
Restore Project

This establishes a single lifecycle-writer principle.

5. Project Catalog

The Project Catalog is a read-only discovery projection of available projects.

Its purpose is to allow the Home Page to efficiently display and search existing projects without loading complete clinical project data.

The Catalog may expose:

list_projects()
get_project_summary(project_id)
search_projects(query)

A ProjectSummary may contain only the information required for discovery, for example:

Project ID
Project Name
Patient Display Name
Status
Procedure
Created At
Updated At
Last Opened At
Thumbnail / Preview Reference

The Catalog must not:

create projects;
modify projects;
delete projects;
persist project state;
implement project lifecycle rules.

The Catalog is a read model, not the project lifecycle owner.

6. Project Catalog Consistency

The Project Catalog may be implemented as a repository query, indexed metadata store, cached projection, filesystem index, database view, or another read-optimized mechanism.

Regardless of implementation, the following contract applies:

The Project Catalog must represent the project set managed by the Project Management subsystem and must not become an independent authoritative project store.

When a project is created, updated, or deleted, the Project Management subsystem is responsible for ensuring that the Catalog can eventually reflect the new state.

The synchronization mechanism is intentionally not fixed by this document.

Possible mechanisms include:

application/domain events;
explicit catalog invalidation;
repository-backed refresh;
controlled cache invalidation;
other deterministic synchronization mechanisms.

Polling or TTL-based caching must not be introduced by the Home Page itself as an independent consistency mechanism.

The precise synchronization strategy should be defined in a dedicated ADR, such as:

adr/project-catalog-synchronization.md

Relevant lifecycle events may include:

ProjectCreated
ProjectUpdated
ProjectDeleted

The Catalog may subscribe to these events or use another approved synchronization mechanism.

7. Home Page

The Home Page is the project discovery and selection interface.

Its responsibilities are:

request the project list;
display project summaries;
search and filter projects;
allow the user to select a project;
request the selected project to be opened;
transfer control to the Workspace.

The Home Page must not:

create projects directly;
modify projects directly;
delete projects directly;
write project files;
access project storage directly;
maintain the authoritative project list;
maintain patient records;
implement project persistence;
implement project lifecycle policy.

The Home Page may initiate a project lifecycle command through the Project Manager, but it must never implement the operation itself.

For example, if a future UI provides a "Delete Project" action:

Home Page
    │
    │ delete request
    ▼
Project Manager
    │
    ├── access check
    ├── validation
    ├── lifecycle rules
    └── repository.delete(...)

The Home Page only represents the user interaction.

8. Project Creation

Project creation is exclusively coordinated by the Project Manager.

A typical sequence is:

User
  │
  ▼
Home Page / Project Creation UI
  │
  ▼
Project Manager
  │
  ├── authorization
  ├── validate input
  ├── generate Project ID
  ├── initialize project
  ├── initialize patient/project metadata
  └── persist
          │
          ▼
   Project Repository
          │
          ▼
    Project Storage

After successful creation, the Project Manager emits the appropriate lifecycle event, such as ProjectCreated.

The Home Page does not manually add the new project to an authoritative list.

9. Project Update

All project-level modifications pass through the Project Manager.

Examples include:

changing project metadata;
changing patient-related project information;
changing project status;
changing project configuration;
renaming a project;
updating project-level workflow state.

Clinical operations performed in the Workspace may modify project data, but those modifications must pass through the appropriate application/domain contracts rather than directly writing project storage.

The Workspace therefore does not become a second project manager.

10. Project Deletion

Project deletion is exclusively controlled by the Project Manager.

A deletion request must pass through the Project Manager, which is responsible for:

authorization;
validation;
dependency checks;
persistence/storage coordination;
deletion of the persistent project representation;
lifecycle event publication;
catalog synchronization.

The Home Page must never delete project folders or files directly.

The Repository and Storage layers perform the physical deletion requested by the Project Manager.

11. Project Storage

Project Storage represents the infrastructure responsible for the physical representation of a project.

An initial filesystem implementation may use a structure such as:

projects/
    <project-id>/
        project.json
        patient_record.json
        imaging/
        models/
        analysis/
        planning/
        documents/

The exact layout is an infrastructure decision.

The domain and application layers must not depend on physical paths such as:

C:/...
/home/...
projects/<id>/...

Project storage may later be implemented using:

local filesystem storage;
database-backed storage;
institutional storage;
remote storage;
another persistence mechanism.

The Project Manager must remain independent of the concrete storage technology.

12. Project Repository

The Project Repository is the persistence abstraction through which the Project Manager loads and stores project state.

Conceptually:

class ProjectRepository(Protocol):
    def create(self, project: Project) -> None: ...
    def get(self, project_id: ProjectId) -> Project: ...
    def update(self, project: Project) -> None: ...
    def delete(self, project_id: ProjectId) -> None: ...
    def exists(self, project_id: ProjectId) -> bool: ...

The repository does not decide:

Should this project be created?
Should this project be deleted?
Is this user allowed to open it?
Which workflow should be selected?

Those are Project Management/application concerns.

The repository provides persistence capabilities to the lifecycle authority.

13. Persistence Representation

A file such as:

patient_record.json

may be used by a filesystem repository, but it is a persistence representation, not an architectural authority.

The application must not be designed around a Patient_Config_Manager that independently owns the patient lifecycle.

Instead:

Project Manager
       │
       ▼
Project Repository
       │
       ▼
Persistence representation

The persistence format may contain:

patient information;
project metadata;
logical resource references;
workflow state;
schema/version information.

The exact serialization contract belongs to the persistence/data documentation.

This distinction allows CranioZ to replace a JSON/filesystem implementation without changing the Project domain model.

14. Project Path Resolution

Filesystem-specific path resolution belongs to infrastructure.

A dedicated service such as a ProjectPathResolver may translate logical project resources into physical paths.

For example:

resolve("imaging/ct")
resolve("models/maxilla")
resolve("planning/splint")

The Workspace and clinical modules must not construct project filesystem paths manually.

This provides a stable abstraction if the physical storage implementation changes.

15. Project Access Policy

Because projects may contain patient-related information, authorization must be evaluated at the Project Management boundary.

The architecture should expose a policy abstraction from the beginning:

class ProjectAccessPolicy(Protocol):
    def can_create(self, actor: Actor) -> bool: ...
    def can_open(self, actor: Actor, project_id: ProjectId) -> bool: ...
    def can_update(self, actor: Actor, project_id: ProjectId) -> bool: ...
    def can_delete(self, actor: Actor, project_id: ProjectId) -> bool: ...

The initial implementation may be an AllowAllProjectAccessPolicy.

The important architectural rule is:

Authorization is evaluated by the Project Management layer, not independently by the Home Page or Workspace.

This establishes the extension point required for future:

user accounts;
roles;
institutional access control;
project permissions;
restricted operations.

Authorization and audit logging are separate concerns, although both operate at the Project Management boundary.

16. Opening a Project

Selecting a project on the Home Page does not mean that the Home Page loads and owns the entire project.

The opening process is:

1. User selects project
          │
          ▼
2. Home Page requests project opening
          │
          ▼
3. Project Manager checks access
          │
          ▼
4. Project Manager loads project
          │
          ▼
5. Project Manager resolves clinical workflow
          │
          ▼
6. Project Manager creates ProjectContext
          │
          ▼
7. Workspace receives ProjectContext
          │
          ▼
8. Workspace initializes the clinical flow

The Project Manager remains the lifecycle authority throughout this process.

17. Project Context

ProjectContext is a runtime initialization context created when a project is opened.

It is not the Project itself.

It is not a persistent domain aggregate.

It does not own the project lifecycle.

It is not required to be serialized as the project's canonical representation.

Its purpose is to provide the Workspace with the information and runtime references necessary to operate on an opened project.

Conceptually:

ProjectContext
├── project_id
├── project_metadata
├── patient_summary
├── workflow_id
├── workflow_config
└── object_references

Runtime services or capabilities required by the Workspace should be supplied through the application's dependency-injection/application-service mechanisms rather than turning ProjectContext into a generic service locator.

Conceptually:

Persistent Project
       │
       │ load
       ▼
Project Manager
       │
       │ creates
       ▼
ProjectContext
       │
       │ + ClinicalWorkflow
       ▼
Workspace

The context exists only while the project is active in the application session.

18. Clinical Workflow Handoff

A Project may be associated with one or more clinical workflows.

Examples include:

Orthognathic Surgery
Facial Implant Planning
Osteosynthesis Planning
Airway Analysis
Cephalometric Analysis
Fibula Reconstruction

The Home Page may allow the user to select a workflow, but it does not execute the workflow.

The Project Manager or an appropriate application service resolves the workflow and supplies it with the Project Context.

Conceptually:

Selected Project
      │
      ├── Project Context
      │
      └── Clinical Workflow
                │
                ▼
            Workspace

The exact workflow/module architecture is defined by the Flow and Module documentation.

19. Workspace

The Workspace is the active clinical execution environment.

It is responsible for:

displaying project data;
executing clinical workflows;
invoking modules;
manipulating domain objects through application commands;
displaying imaging and 3D data;
executing planning operations;
managing workspace layout;
maintaining temporary UI state;
presenting clinical tools.

The Workspace must not:

create independent projects;
delete projects directly;
maintain the authoritative project list;
implement project persistence;
decide project lifecycle policy;
manage patient/project storage;
become a second Project Manager.

The Workspace consumes the Project Context provided by the Project Management layer.

20. Clinical Data Changes from the Workspace

Clinical operations performed in the Workspace may produce persistent project changes.

For example:

Workspace
    │
    │ Apply Le Fort I osteotomy
    ▼
Application Command
    │
    ▼
Planning / Domain Service
    │
    ▼
Project State
    │
    ▼
Persistence Boundary

The Workspace must not perform direct persistence such as:

open("project.json", "w")

or equivalent storage operations.

Clinical modules must also not access project storage directly.

They must use the application/domain contracts provided by CranioZ.

21. Closing a Project

Closing a project is a runtime lifecycle operation controlled by the Project Manager.

Closing a project means ending the active runtime context associated with the project.

A close operation may involve:

checking for pending changes;
persisting changes according to the configured persistence/autosave policy;
publishing a ProjectClosing event;
releasing project-specific runtime resources;
invalidating the active ProjectContext;
publishing ProjectClosed.

Closing a project does not remove it from the Project Catalog.

Open
  │
  ▼
Active ProjectContext
  │
  ▼
Close
  │
  ├── persist pending state
  ├── release runtime resources
  └── dispose context
  │
  ▼
Project remains persisted and discoverable

Closing is therefore distinct from deletion.

Whether another project can be opened before the current project is closed is an application/session policy and should not be implemented independently by the Home Page.

22. Project Events

Project lifecycle changes may be communicated through the Application Event Bus.

Relevant events may include:

ProjectCreated
ProjectOpened
ProjectUpdated
ProjectClosing
ProjectClosed
ProjectDeleted

Events communicate state changes; they do not transfer ownership.

For example:

Project Manager
      │
      ▼
Application Event Bus
      │
      ├── Project Catalog
      ├── Home Page
      ├── Workspace
      └── other subscribers

The Workspace may react to ProjectOpened or ProjectClosed, but it does not become the lifecycle authority.

The exact event semantics belong to the application/event documentation.

23. Who Reads the Project?

Different components read different representations.

Project Catalog

Reads lightweight project metadata for discovery:

ProjectSummary
Project Manager

Reads the authoritative project state when opening or managing a project:

Project
Workspace

Receives the active runtime representation through:

ProjectContext
Clinical Modules

Consume project/domain data through their defined application contracts.

The Home Page and Workspace must not bypass the Project Management boundary to read arbitrary project files.

24. Who Stores the Project?

The responsibilities are deliberately separated:

Project Manager
    = lifecycle authority and coordinator

Project Repository
    = persistence abstraction

Project Storage
    = physical storage infrastructure

Project Catalog
    = read-only discovery projection

Project Context
    = active runtime context

Home Page
    = discovery and selection UI

Workspace
    = clinical execution environment

This distinction prevents infrastructure classes from becoming business authorities and prevents UI components from becoming persistence layers.

25. Single Lifecycle Writer Principle

CranioZ follows a single lifecycle writer principle for projects.

Only the Project Manager may perform authoritative project lifecycle mutations.

This does not mean that only one class in the entire system may ever change domain objects.

Clinical modules and application services may modify clinical domain state through their defined commands and services.

The rule means that there is only one authoritative application boundary for:

Create Project
Open Project
Update Project Metadata
Close Project
Delete Project
Archive Project
Restore Project

The following components must not independently implement project lifecycle behavior:

Home Page
Workspace
Clinical Modules
Plugins
Project Catalog
Project Repository
Project Storage

Plugins and modules must use the public Project Management/application API.

26. Concurrency and Consistency

Project-level concurrency is a Project Management and persistence concern.

Potential mechanisms include:

filesystem locking;
optimistic concurrency;
project revision numbers;
transactions;
conflict detection;
recovery after interrupted writes;
autosave coordination.

This document establishes the responsibility boundary but intentionally does not select a concurrency strategy.

A dedicated ADR should define the chosen model:

adr/project-concurrency.md

The eventual implementation should ensure that concurrent project modifications cannot silently corrupt persistent clinical data.

27. Error Handling

Project lifecycle failures should be represented by application-level errors.

Examples include:

ProjectNotFound
ProjectAlreadyExists
ProjectValidationError
ProjectStorageError
ProjectCorrupted
ProjectAccessDenied
ProjectInUse
ProjectDeletionError
ProjectConcurrencyError

The Home Page should present appropriate user-facing feedback but should not interpret infrastructure-specific exceptions.

The Workspace should similarly receive application-level failures rather than depending directly on filesystem or database exceptions.

28. Security, Privacy, and Auditability

Projects may contain patient-related information and therefore require architectural support for access control and auditability.

The Project Management boundary should provide extension points for:

authorization;
role-based access;
project permissions;
audit events;
controlled deletion;
data export;
data retention;
institutional storage policies.

Authorization is represented by ProjectAccessPolicy.

Audit logging should consume application/project events rather than being implemented by the Home Page or Workspace.

The initial implementation may use permissive access and minimal auditing, but the extension points should exist from the beginning.

29. Project Lifecycle

The conceptual project lifecycle is:

                ┌───────────────┐
                │    Create     │
                └───────┬───────┘
                        ▼
                ┌───────────────┐
                │    Persist    │
                └───────┬───────┘
                        ▼
                ┌───────────────┐
                │     Open      │
                └───────┬───────┘
                        ▼
                ┌───────────────┐
                │    Active     │
                │ ProjectContext│
                └───────┬───────┘
                        │
                 ┌──────┴──────┐
                 │             │
                 ▼             ▼
              Update         Close
                 │             │
                 │             ▼
                 │       ┌───────────────┐
                 └──────►│   Persisted   │
                         └───────┬───────┘
                                 │
                                 ▼
                              Delete

The exact project status model belongs to the Project domain documentation.

30. Architectural Invariants

The following rules are mandatory:

The Project Manager is the single application-level authority for project lifecycle.
The Home Page is read-only with respect to project lifecycle state.
The Workspace is not a project manager.
The Home Page does not directly access project persistence.
The Workspace does not directly access project persistence.
The Project Catalog is read-only.
The Project Repository is a persistence abstraction, not a lifecycle authority.
Project Storage is infrastructure, not business logic.
Project creation goes through the Project Manager.
Project deletion goes through the Project Manager.
Project metadata maintenance goes through the Project Manager.
Project opening goes through the Project Manager.
Project closing is controlled by the Project Manager.
The Project Context is not the Project itself.
The Project Context does not own the project lifecycle.
Patient is a domain entity; there is no separate Patient Manager in this architecture.
Patient-related project data is managed within the Project Management boundary.
The authoritative project list is not maintained by the Home Page.
Plugins and modules must not bypass the Project Management/application API.
Project lifecycle changes may be communicated through application events.
Catalog synchronization must not be implemented independently by the Home Page.
Authorization is evaluated at the Project Management boundary.
Physical storage paths are infrastructure concerns.
Clinical workflow execution belongs to the Workspace/Flow/Module architecture, not to Project Management.
31. Conceptual API

The exact implementation belongs to the application layer, but the Project Manager should conceptually expose operations similar to:

class ProjectManager(Protocol):
    def create_project(...) -> Project: ...
    def open_project(project_id: ProjectId) -> ProjectContext: ...
    def update_project(...) -> None: ...
    def close_project(project_id: ProjectId) -> None: ...
    def delete_project(project_id: ProjectId) -> None: ...

The read-only Catalog may expose:

class ProjectCatalog(Protocol):
    def list_projects(...) -> list[ProjectSummary]: ...
    def get_project_summary(
        self,
        project_id: ProjectId,
    ) -> ProjectSummary: ...
    def search_projects(
        self,
        query: str,
    ) -> list[ProjectSummary]: ...

Persistence remains behind:

class ProjectRepository(Protocol):
    def create(self, project: Project) -> None: ...
    def get(self, project_id: ProjectId) -> Project: ...
    def update(self, project: Project) -> None: ...
    def delete(self, project_id: ProjectId) -> None: ...

These interfaces describe responsibility boundaries rather than prescribing concrete implementation details.

32. Project Lifecycle Sequence

The normal user flow is:

The Workspace then executes the selected clinical workflow.

33. Creation and Persistence Sequence

The Home Page receives the updated discovery state through the Catalog mechanism rather than maintaining its own authoritative list.

34. Closing and Opening Projects

Opening and closing are runtime lifecycle operations.

Closing does not delete the Project.

Deleting does not represent a normal workspace transition and is controlled exclusively by the Project Manager.

35. Relationship to Other Architecture Documents

This document defines the application-level project lifecycle and ownership model.

It should be read together with:

domain/patient.md — Patient domain entity;
domain/project.md — Project domain representation;
domain/scene.md — Scene and object membership;
domain/objects.md / Datatypes documentation — domain object model;
application/ documentation — application services, commands, events, and orchestration;
infrastructure/ documentation — storage and persistence implementations;
flows/ documentation — clinical workflow execution;
modules/ documentation — module lifecycle and contracts;
workspace.md — Workspace lifecycle and runtime context;
adr/ — architectural decisions governing persistence, concurrency, transactions, catalog synchronization, and access control.
36. Related Architectural Decisions

The following topics should be defined by dedicated ADRs rather than overloaded into this document:

Project Catalog Synchronization
Project Concurrency
Project Persistence Format
Project Access and Audit
Project Transactions
Project Recovery / Autosave

The project.md document defines the stable responsibility boundaries. ADRs define implementation-specific or decision-sensitive policies.

37. Summary

CranioZ treats the Project as the central persistent clinical container and establishes a single application-level authority for its lifecycle.

The resulting architecture is:

Project Manager
    │
    ├── Project Access Policy
    ├── Project Repository
    │       └── Project Storage
    │
    ├── Application Events
    │
    └── Project Context
             │
             └── Clinical Workflow
                       │
                       ▼
                   Workspace
                       │
                       ▼
                 Clinical Modules


Project Catalog
      │
      ▼
  Home Page
      │
      │ select
      ▼
Project Manager

The central responsibilities are:

Project Manager
    Owns lifecycle.

Project Catalog
    Provides read-only discovery.

Project Repository
    Provides persistence.

Project Storage
    Provides physical storage.

Project Access Policy
    Provides authorization.

Project Context
    Provides the active runtime context.

Home Page
    Discovers and selects projects.

Workspace
    Executes clinical workflows.

The architectural principle is:

The Home Page discovers projects, the Project Manager owns their lifecycle, the Repository persists them, Storage provides the physical representation, the Project Context represents the active runtime state, and the Workspace executes the selected clinical workflow without managing the project.
"""

path = Path("/mnt/data/project.md")
path.write_text(content, encoding="utf-8")
print(path)