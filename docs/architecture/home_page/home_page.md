# Homepage

## 1. Purpose

The **Homepage** is the application's entry point and catalog interface.

It is displayed when CranioZ starts without an active Project and provides a lightweight interface for browsing available Projects and Flow definitions.

The Homepage does **not** create, modify, save, or delete Projects. It does not manipulate Project files, directories, clinical data, or domain objects.

Instead, the Homepage presents available information and dispatches user intentions to the appropriate Application services.

The core principle is:

> **The Homepage displays information and initiates actions; Application services execute those actions.**

The Homepage therefore acts as a presentation and navigation layer between the user and the application.

---

# 2. Architectural Role

The Homepage belongs to the UI layer.

Its role is intentionally limited to:

* presenting available Projects;
* presenting available Flow definitions;
* receiving user interactions;
* initiating application commands;
* presenting operation results and errors;
* navigating the user to the appropriate application state.

The Homepage does not contain Project-management business logic.

Conceptually:

```text
User
 │
 ▼
Homepage
 │
 ├── Display Projects
 ├── Display Flows
 ├── Capture user actions
 └── Dispatch commands
          │
          ▼
     Application Layer
          │
     ┌────┴───────────────┐
     │                    │
Project Manager      Flow Manager
     │                    │
     ▼                    ▼
 Project              Flow System
```

---

# 3. Responsibilities

The Homepage is responsible for:

* displaying existing Projects;
* displaying Project metadata required for navigation;
* displaying available Flow definitions;
* displaying recent Projects;
* providing actions such as **New Project** and **Open Project**;
* dispatching user intentions to the appropriate Application services;
* displaying operation status and errors;
* providing access to application-level settings and documentation;
* transitioning the user between the Homepage and the active Workspace.

The Homepage is not responsible for executing the underlying operations.

---

# 4. Non-Responsibilities

The Homepage does not:

* create Projects;
* open Project data;
* modify Projects;
* save Projects;
* delete Projects;
* manipulate Project directories;
* manipulate Project files;
* load DICOM data;
* load meshes;
* manage clinical objects;
* execute clinical Modules;
* execute clinical Flows;
* modify the Scene;
* manage Project persistence;
* implement Project business rules.

These responsibilities belong to the appropriate Application, Domain, and Infrastructure components.

---

# 5. Project Catalog

The Homepage presents a catalog of Projects that already exist.

The catalog provides lightweight information required for navigation and identification, such as:

* Project name;
* Project identifier;
* Project location or reference;
* last opened date;
* Project status;
* associated metadata when available.

The Homepage does not load the complete Project merely to display it.

Large resources such as:

* DICOM studies;
* volumetric images;
* surface meshes;
* facial scans;
* segmentation data;
* planning objects;

are loaded only when required by the Project-opening and Workspace initialization process.

The Project catalog therefore remains lightweight.

---

# 6. Project Discovery

The Homepage should obtain Project information through the appropriate Application service or Project catalog interface.

It should not directly scan filesystem directories or read Project files.

Conceptually:

```text
Homepage
    │
    │ request Project list
    ▼
Application / Project Catalog
    │
    ▼
Project Repository / Infrastructure
    │
    ▼
Project metadata
    │
    ▼
Homepage
```

This keeps the Homepage independent from the physical storage implementation.

A Project may be stored in the default CranioZ Project Root or in another supported location. The Homepage should not depend on a specific filesystem layout.

---

# 7. Flow Catalog

The Homepage may display the Flow definitions available to CranioZ.

A **Flow** represents an ordered clinical workflow composed of Modules.

Examples include:

* Orthognathic Surgery;
* Facial Implant Planning;
* Rhinoplasty Planning;
* Custom Flow.

The Homepage only displays and provides access to Flow definitions.

It does not execute a Flow.

Flow execution occurs in the active Project and Workspace.

Conceptually:

```text
Homepage
    │
    │ request available Flows
    ▼
Flow Manager / Flow Registry
    │
    ▼
Flow Definitions
    │
    ▼
Homepage
```

---

# 8. Project Actions

The Homepage may provide controls for Project-related actions.

These controls are **entry points**, not implementations of Project operations.

For example:

```text
[ New Project ]
```

does not create a Project inside the Homepage.

Instead:

```text
Homepage
    │
    │ New Project requested
    ▼
Project Manager
    │
    ▼
Project Creation Workflow
```

The same principle applies to opening, closing, or deleting a Project.

The Homepage only dispatches the corresponding request.

---

# 9. New Project

The Homepage provides a **New Project** action.

The action delegates Project creation to the **Project Manager**.

```text
[ New Project ]
       │
       ▼
Project Manager
       │
       ├── Collect Project information
       ├── Validate request
       ├── Create Project
       ├── Initialize Project metadata
       └── Initialize Project storage
       │
       ▼
Workspace
```

The Homepage does not:

* create the Project directory;
* create `project.json`;
* initialize Project metadata;
* write Project files;
* validate Project persistence;
* manage the Project filesystem.

After successful Project creation, the Application layer may transition the user to the Workspace.

---

# 10. Open Project

The Homepage provides an **Open Project** action.

The action is delegated to the Project Manager.

```text
[ Open Project ]
       │
       ▼
Project Manager
       │
       ├── Select Project
       ├── Validate Project
       ├── Load Project context
       └── Initialize Project
       │
       ▼
Workspace
```

The Homepage does not directly load Project files or clinical resources.

Project loading and validation are responsibilities of the Project Manager and the underlying Application and Infrastructure services.

---

# 11. Recent Projects

The Homepage may display recently opened Projects.

Recent Project information should remain lightweight.

Example:

```text
Recent Projects

Case 001
Case 002
Case 003
```

Additional metadata may be displayed when useful:

```text
Case 001
Last opened: 2026-10-02
```

The recent-project list is an application-level navigation aid.

It is not part of the Project's clinical data.

The Homepage may request that the Application layer resolve a recent Project, but it does not directly manipulate the Project storage.

If a recent Project is no longer available, the Homepage should present an appropriate message and allow the user to remove or dismiss the stale entry through the appropriate application service.

---

# 12. Project Root

CranioZ provides a default Project Root:

```text
C:\Users\<user>\Documents\CranioZ\Projects
```

This is the default location for Projects created through the application.

The default Project Root is an application setting and may be changed by the user.

Projects may also exist outside the default location.

For example:

```text
C:\Users\<user>\Documents\CranioZ\Projects\
├── Case_001\
├── Case_002\
└── Case_003\
```

or:

```text
D:\ClinicalData\CranioZ\
├── Case_004\
└── Case_005\
```

The Homepage does not assume that all Projects exist in a single physical directory.

The storage location is resolved by the appropriate Project and Application services.

---

# 13. Project Selection

Selecting a Project on the Homepage does not load or modify the Project.

The selection produces an application-level request.

Conceptually:

```text
User selects Project
        │
        ▼
Homepage
        │
        │ Project selected
        ▼
Project Manager
        │
        ▼
Open Project
        │
        ▼
Workspace
```

The Homepage should not pass filesystem paths as its primary application contract.

Project identity should preferably be represented by a stable Project identifier or application-level reference, leaving storage resolution to the Project Manager.

---

# 14. Flow Selection

The Homepage may allow the user to select a Flow before entering the Workspace.

Flow selection represents an intended workflow and does not execute the Flow.

Conceptually:

```text
User
 │
 ▼
Select Project
 │
 ▼
Select Flow
 │
 ▼
Project Manager / Application
 │
 ▼
Workspace
 │
 ▼
Activate selected Flow
```

The exact relationship between Project selection and Flow selection is determined by the Application layer.

The Homepage only captures and dispatches the user's selection.

---

# 15. Navigation to the Workspace

The Workspace is the active Project environment.

After a Project has been successfully opened or created, the Application layer transfers control from the Homepage to the Workspace.

```text
Homepage
    │
    ▼
Project Manager
    │
    ▼
Active Project
    │
    ▼
Workspace
```

The Workspace is responsible for:

* displaying Project data;
* managing the active Scene;
* displaying Viewports;
* executing Modules;
* executing Flows;
* managing clinical planning interactions.

The Homepage remains outside the active clinical environment.

---

# 16. Returning to the Homepage

When the user closes the active Project, the Application layer releases the Project context and returns the application to the Homepage.

Conceptually:

```text
Workspace
    │
    ▼
Close Project
    │
    ▼
Application / Project Manager
    │
    ├── Handle pending changes
    ├── Release Project resources
    └── Clear active Project context
    │
    ▼
Homepage
```

The Homepage does not perform Project closing or persistence operations.

It simply becomes the visible application state after the active Project has been closed.

---

# 17. Unsaved Changes

If the active Project contains pending changes, the Application layer is responsible for determining the appropriate action before the Project is closed.

Possible options include:

```text
Project has unsaved changes.

[ Save and Close ]
[ Close Without Saving ]
[ Cancel ]
```

The Homepage does not implement saving.

Persistence and transaction handling belong to the Application and Infrastructure layers.

The Homepage only receives and displays the resulting state.

---

# 18. Error Handling

The Homepage should present clear user-facing feedback when an Application operation fails.

Possible errors include:

* Project not found;
* Project metadata unavailable;
* unsupported Project version;
* invalid Project;
* insufficient access;
* Project loading failure;
* Flow unavailable;
* unexpected application error.

Example:

```text
Unable to open Project.

The Project metadata is invalid or unsupported.

[ Details ]    [ OK ]
```

Technical diagnostic information should be available through the application's logging and diagnostic mechanisms.

The Homepage should not interpret or recover from low-level infrastructure errors itself.

---

# 19. Application Menu

The Homepage may expose application-level functionality through the application menu.

Possible entries include:

```text
Application
├── New Project
├── Open Project
├── Recent Projects
├── Settings
├── Documentation
├── Check for Updates
└── Exit
```

These menu items follow the same architectural rule as Homepage buttons: they initiate Application-level actions but do not implement them.

---

# 20. Settings

Application settings are global to the CranioZ installation or user environment.

Examples include:

* language;
* theme;
* default Project Root;
* rendering preferences;
* cache location;
* update preferences;
* logging preferences;
* optional integrations.

The Homepage may provide access to these settings but does not manage their persistence.

Project-specific configuration belongs to the Project and is handled by the appropriate Project services.

---

# 21. Architectural Integration

The Homepage interacts with Application-level services through defined interfaces.

A simplified model is:

```text
                         UI
                          │
                    ┌─────┴─────┐
                    │ Homepage  │
                    └─────┬─────┘
                          │
                    User actions
                          │
                          ▼
                    Application
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   Project Manager   Flow Manager   Other Services
          │               │
          ▼               ▼
     Project System   Flow System
          │
          ▼
   Infrastructure
```

The Homepage should depend on stable Application-level contracts rather than on concrete storage or domain implementations.

---

# 22. Architectural Boundary

The Homepage should remain intentionally lightweight.

Its responsibilities can be summarized as:

```text
Homepage
    │
    ├── Display
    ├── Present
    ├── Select
    ├── Navigate
    └── Dispatch
          │
          ▼
     Application Layer
```

It should not become a secondary Project Manager or clinical Workspace.

The following principle should guide implementation:

> **If an operation changes Project state, the operation does not belong to the Homepage.**

The Homepage may provide the button, menu item, or interaction that requests the operation, but execution belongs to the appropriate Application service.

---

# 23. Initial Implementation Scope

The initial Homepage implementation should provide:

1. Application startup.
2. Project catalog display.
3. Recent Project display.
4. Flow catalog display.
5. New Project action.
6. Open Project action.
7. Project selection.
8. Flow selection.
9. Navigation to the Workspace.
10. Return to the Homepage after Project closure.
11. Application-level settings and documentation access.

The following should remain outside the Homepage implementation:

* Project persistence;
* Project filesystem management;
* clinical data processing;
* DICOM processing;
* mesh processing;
* segmentation;
* registration;
* cephalometric analysis;
* osteotomy planning;
* splint generation;
* clinical Flow execution.

---

# 24. Core Navigation Model

The fundamental application navigation is:

```text
                         Homepage
                            │
             ┌──────────────┼──────────────┐
             │              │              │
       [New Project]   [Open Project]   [Select Flow]
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    Application Layer
                            │
                   ┌────────┴────────┐
                   │                 │
            Project Manager    Flow Manager
                   │                 │
                   └────────┬────────┘
                            ▼
                       Active Project
                            │
                            ▼
                        Workspace
                            │
                     Clinical Work
                            │
                            ▼
                      Close Project
                            │
                            ▼
                         Homepage
```

The Homepage is therefore the **entry point and presentation/catalog layer** of CranioZ.

It displays Projects and Flow definitions, captures user intentions, and delegates operations to the Application layer.

It does not create, modify, save, delete, or directly load Projects.
