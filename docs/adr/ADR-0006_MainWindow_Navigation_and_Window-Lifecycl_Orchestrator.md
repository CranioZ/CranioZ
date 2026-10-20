# ADR-0006: MainWindow as the Navigation and Window-Lifecycle Orchestrator
Status: Accepted
Date: 2026-10-20
Deciders: Architecture team
Related: main_window.md, home_page.md, workspace.md, ADR-0001, ADR-0002, ADR-0005

## 1. Context
main_window.md §2 states that MainWindow "forwards project open and close requests to the application runtime without managing the project lifecycle or project data." §9 states that "user actions are forwarded through Application-layer capabilities rather than performing domain operations inside window callbacks."

The document is correct at the level of responsibilities, but it does not specify:

* Which component listens to the "Start" signal emitted by the Home Page and initiates the open-project flow.
* Which component creates and destroys the Workspace widget.
* Whether the "Home" button located in the Workspace's Top Overlay calls ProjectManager.close_project() directly or emits an intention.
* Where the "Home" button is injected into the Top Overlay.
* Whether the Workspace orchestrates its own lifecycle by listening to events.

During the design of piece 7.6b (MainWindow + Home↔Workspace navigation), three readings coexisted:

Reading A — The button executes.
The "Home" button calls ProjectManager.close_project() directly. Rejected: it mixes UI with Application concerns, and the button would need to know about ProjectManager, ProjectContext, and the current project id.

Reading B — The Workspace orchestrates itself.
The Workspace listens to ProjectClosing on the EventBus and destroys itself. Rejected: the Workspace is a Qt widget; making it observe application events to self-destruct couples it to the event system and violates the ownership boundary (a widget does not own its own lifecycle beyond Qt's parent-child mechanism).

Reading C — MainWindow orchestrates.
MainWindow listens to the "Start" signal, calls ProjectManager, creates the Workspace, injects the "Home" button, listens to the button's clicked, calls ProjectManager.close_project(), and destroys the Workspace. This ADR adopts Reading C.

The ambiguity must be resolved before piece 7.6b is implemented, because the boundary determines which component holds ProjectManager references, which component creates widgets, and which component is testable without Qt.

## 2. Decision
2.1 The "Home" button is a navigation link, not a command
The button emits clicked() and nothing else. It:

* Does not call ProjectManager.close_project().
* Does not destroy the Workspace.
* Does not modify the QStackedWidget.
* Does not know ProjectContext, ProjectManager, Workspace, or the current project id.
* The semantics of "the user wants to return to the Home Page" belong to MainWindow.

### 2.2 MainWindow is the sole orchestrator of navigation and window lifecycle
MainWindow is the only component that knows HomePage, Workspace, and ProjectManager simultaneously. It:

* Listens to HomePage.project_open_requested(project_id, flow_id).
* Calls ProjectManager.open_project(actor, project_id, workflow_id=flow_id).
* Creates Workspace(..., project_context=context).
* Injects the "Home" button into the Workspace's TopOverlay via set_left_content(widget).
* Listens to the button's clicked.
* Calls ProjectManager.close_project(actor, project_id).
* Destroys the Workspace.
* Returns to HomePage and calls HomePage.refresh().
* No other component performs these steps.

### 2.3 The TopOverlay is a container, not an orchestrator
TopOverlay.set_left_content(widget) accepts a widget. The method:

* Reparents the widget to the left segment.
* Places it in the segment's QHBoxLayout.
* Replaces any previous content.
* Does not know what the widget does.

set_center_content and set_right_content are not added in piece 7.6b. They will be added when the Top Bar composition requires them (piece 7.6c).

### 2.4 The Workspace is created and destroyed by MainWindow
The Workspace:

* Does not create itself.
* Does not destroy itself.
* Does not listen to application events to react to project closure.
* Receives ProjectContext at construction.
* Materializes a ModuleUISpec when load_spec() is called.
* MainWindow owns the Workspace instance for the duration of the open project.

### 2.5 MainWindow does not implement business rules
MainWindow coordinates. It does not:

* Decide whether a project may be opened (that is ProjectManager + ProjectAccessPolicy).
* Validate a project (that is ProjectRepository + ProjectMetadata).
* Render project-specific UI (that is Workspace + Editors + Toolbars).
* Evaluate workflow requirements (that is the Flow engine, Bloco 9).
* MainWindow listens to signals and calls Application services.

### 2.6 MainWindow receives ProjectManager and Actor at construction
MainWindow's constructor accepts:

* catalog: ProjectCatalog
* manager: ProjectManager
* actor: Actor
* 
The registries and services required to construct a Workspace: EditorRegistry, ToolRegistry, ThemeService.

The actor is injected by the bootstrap. MainWindow does not construct one, and does not use a hardcoded value. When the application gains a user model, the bootstrap injects the logged user's identity; MainWindow does not change.

## 3. Rationale
### 3.1 Separation of responsibilities
* The "Home" button is pure UI. It must not know ProjectManager.
* TopOverlay is a generic container. It must not know navigation signals.
* HomePage is a discovery screen. It must not know ProjectManager (home_page.md §4).
* Workspace is a Qt widget. It must not orchestrate its own project lifecycle.
* ProjectManager is an Application service. It must not know Qt widgets.
* MainWindow is the only component whose responsibility is to know both sides: UI widgets and Application services.

### 3.2 Widget lifecycle vs. project lifecycle
These are distinct:

* Project lifecycle: ProjectManager.open_project / close_project. Owns ProjectContext, publishes events, validates access.
* Widget lifecycle: MainWindow creates and destroys Workspace. Owns Qt parent-child relationships, signal connections, and the QStackedWidget.
* Conflating them is what produces Reading A and Reading B. Separating them makes each component testable in isolation:
* ProjectManager is testable without Qt.
* Workspace is testable with a ProjectContext and a ModuleUISpec, without a ProjectManager.
* HomePage is testable with a ProjectCatalog, without a ProjectManager.

MainWindow is testable with an InMemoryProjectRepository and a Workspace, without filesystem.

### 3.3 Consistency with existing ADRs
ADR-0001 establishes Area ≠ Editor. The Workspace hosts Areas but does not own the project lifecycle. This ADR extends that: MainWindow owns the Workspace, not the other way around.

ADR-0002 establishes that LayoutBuilder is pure and LayoutRenderer materializes widgets. This ADR does not change that. MainWindow does not materialize; it creates the Workspace and hands it a ModuleUISpec.

ADR-0005 establishes that the Top Bar is a structural component materialized as a floating Overlay. This ADR adds set_left_content as the injection point, consistent with the Top Bar being a container, not an orchestrator.

### 3.4 Prevention of anti-patterns
    Anti-pattern	                            Violation	                                                Mitigation
    Home button calls close_project	            main_window.md §9	                                        Button emits clicked; MainWindow handles.
    TopOverlay emits home_requested	            main_window.md §3 (MainWindow does not interpret Top Bar)	TopOverlay accepts arbitrary widgets; no navigation signals.
    ProjectManager creates/destroys Workspace	main_window.md §2 (does not manage project lifecycle)	    ProjectManager does not import Qt. MainWindow owns the widget.
    HomePage creates Workspace	home_page.md §4 (does not execute Modules/Flows)	HomePage.__init__ receives only ProjectCatalog.
    Workspace listens to ProjectClosing to self-destruct	Violates single-owner of widget lifecycle	    Workspace is created and destroyed by MainWindow.
## 4. Consequences
### 4.1 Positive
* Explicit boundaries. Each component has one responsibility.
* TopOverlay is generic. It can receive menus, tabs, settings in future pieces without structural change.
* The "Home" button is trivial. It can be replaced by a QToolButton with an SVG icon without affecting the rest.
* Workspace is reusable. It can be constructed in other contexts (layout preview, visual debug) with a ProjectContext and a ModuleUISpec, without a ProjectManager.
* Testability. MainWindow is testable with an InMemoryProjectRepository; each sub-widget is testable with only the dependencies it declares.

### 4.2 Negative
* MainWindow accumulates signal connections. 14 signals from HomePage plus 1 from the "Home" button = 15 connections. Acceptable: each signal delegates to a single action.
* TopOverlay gains set_left_content. Minor addition. The other segments remain unfilled in piece 7.6b.

### 4.3 Neutral
The "Home" button is a QPushButton("Home") in piece 7.6b. When the Icon Manager exists, it becomes a QToolButton with an SVG. MainWindow's code does not change.

## 5. Rejected alternatives
### 5.1 Home button calls ProjectManager.close_project directly
Rejected. Violates main_window.md §9. Couples the button to Application services. Makes the button untestable without a ProjectManager.

### 5.2 TopOverlay exposes home_requested as its own signal
Rejected. Violates main_window.md §3. TopOverlay is a container, not a navigation component. The QPushButton inside it emits clicked; MainWindow connects to that.

### 5.3 HomePage creates the Workspace
Rejected. Violates home_page.md §4. HomePage would need to know LayoutBuilder, EditorRegistry, ThemeService, and ProjectManager. It does not.

### 5.4 ProjectManager creates/destroys the Workspace
Rejected. Violates main_window.md §2. ProjectManager belongs to the Application layer; Workspace belongs to the UI. ProjectManager must not import Qt.

### 5.5 Workspace self-destructs by listening to ProjectClosing
Rejected. Violates single ownership of widget lifecycle. A widget does not own its own lifecycle beyond Qt parent-child. Making it observe application events to self-destruct couples it to the event system.

### 5.6 MainWindow uses a hardcoded Actor
Rejected. The actor is injected by the bootstrap. When the application gains a user model, the bootstrap changes; MainWindow does not.

## 6. Rules applied by this ADR
1. The "Home" button emits clicked. It does not execute close_project, destroy the Workspace, or modify the QStackedWidget.
2. MainWindow is the sole orchestrator of Home↔Workspace navigation.
3. MainWindow listens to HomePage.project_open_requested, calls ProjectManager.open_project, creates Workspace, injects the "Home" button, listens to its clicked, calls ProjectManager.close_project, destroys Workspace, returns to HomePage, and calls HomePage.refresh().
4. TopOverlay.set_left_content(widget) injects content into the left segment. set_center_content and set_right_content are deferred to piece 7.6c.
5. TopOverlay does not know navigation signals.
6. MainWindow creates and destroys the Workspace.
7. The Workspace receives ProjectContext at construction and materializes ModuleUISpec on load_spec(). It does not orchestrate its own lifecycle.
8. MainWindow does not implement business rules. It delegates to ProjectManager.
9. HomePage receives only ProjectCatalog. It does not receive ProjectManager.
10. Workspace does not know ProjectManager, HomePage, or the "Home" button.
11. ProjectManager does not import Qt and does not create/destroy widgets.
12. MainWindow receives ProjectManager and Actor at construction. It does not construct either.

## 7. Example

    class MainWindow(QMainWindow):
        def __init__(
            self,
            catalog: ProjectCatalog,
            manager: ProjectManager,
            actor: Actor,
            editor_registry: EditorRegistry,
            tool_registry: ToolRegistry,
            theme_service: ThemeService,
        ) -> None:
            super().__init__()
            self._catalog = catalog
            self._manager = manager
            self._actor = actor
            self._editor_registry = editor_registry
            self._tool_registry = tool_registry
            self._theme_service = theme_service
    
            self._current_project_id: ProjectId | None = None
            self._workspace: Workspace | None = None
    
            self._home = HomePage(catalog)
            self._home.project_open_requested.connect(self._on_project_open_requested)
    
            self._stack = QStackedWidget()
            self._stack.addWidget(self._home)
            self.setCentralWidget(self._stack)
    
        def _on_project_open_requested(
            self,
            project_id: ProjectId,
            flow_id: str,
        ) -> None:
            try:
                context = self._manager.open_project(
                    self._actor,
                    project_id,
                    workflow_id=flow_id,
                )
            except ProjectError as exc:
                QMessageBox.critical(self, "Cannot open project", str(exc))
                return
    
            workspace = Workspace(
                editor_registry=self._editor_registry,
                tool_registry=self._tool_registry,
                theme_service=self._theme_service,
                project_context=context,
            )
            home_button = QPushButton("Home")
            home_button.clicked.connect(self._on_home_clicked)
            workspace.top_overlay().set_left_content(home_button)
    
            self._stack.addWidget(workspace)
            self._stack.setCurrentWidget(workspace)
            self._workspace = workspace
            self._current_project_id = project_id
    
            workspace.load_spec(WorkspaceSpec.DEFAULT)
    
        def _on_home_clicked(self) -> None:
            if self._current_project_id is None or self._workspace is None:
                return
            self._manager.close_project(self._actor, self._current_project_id)
            self._stack.removeWidget(self._workspace)
            self._workspace.deleteLater()
            self._workspace = None
            self._current_project_id = None
            self._stack.setCurrentWidget(self._home)
            self._home.refresh()

_on_home_clicked is the only place that closes the project, destroys the Workspace, and returns to the Home Page. The "Home" button only triggered clicked.