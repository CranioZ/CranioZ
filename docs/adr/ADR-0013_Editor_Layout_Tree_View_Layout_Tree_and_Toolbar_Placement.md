# ADR-0013: Editor Layout Tree, View Layout Tree, and Toolbar Placement

**Status:** Accepted (Revised)
**Date:** 2026-10-30 (Revised: 2026-11-09)
**Deciders:** Architecture team
**Related:** ADR-0001_Area_and_Editor.md, ADR-0002_EditorContext_and_Toolbar_Materialization.md, editors.md, workspace.md, toolbar.md, tools.md

---

## 1. Context

ADR-0001 established that Area and Editor are distinct concepts: the Area is a structural container, and the Editor is a functional unit hosted inside it. The Area manages its Editors via an internal Editor Layout Tree, and there is no _EditorHost_.

ADR-0002 established that Toolbars are internal to an Editor, not to an Area, and that the LayoutRenderer materializes Toolbars from the Editor's _toolbar_specs()_.

Together, these two ADRs define the relationship Area → Editor → Toolbar. But they leave three gaps that have caused ambiguity in the codebase, in the prototype, and in the current AreaWidget implementation:

1. **Editor Layout Tree rendering.** ADR-0001 defines the tree, but does not specify how it is rendered (nested QSplitter, QTabWidget, or something else). The current AreaWidget uses QTabWidget (tabs at the bottom of the Area). ADR-0001 §2 says "each Split is rendered as a QSplitter", but the rationale (§3.1, §4.1) cites the prototype's tabs as evidence. This inconsistency has propagated into the code.
2. **Editor vs. View.** ADR-0001 lists Viewport3D and MPR Viewer as examples of Editors. But the prototype shows them as views inside a larger Editor (e.g., the TomographyEditor hosts Axial, Coronal, Sagittal, and 3D views). ADR-0001 does not define a "View" concept, and the codebase has no View abstraction. As a result, Viewport3DEditor and MPRViewerEditor are currently both Editors and views, which conflates two distinct concepts.
3. **Toolbar placement.** ADR-0002 says Toolbars are internal to an Editor, but does not specify where they sit inside the Editor. The prototype (Prototipagem_UI_17) shows Toolbars adjacent to the Views, toggling their visibility based on the active View. The current ToolbarSpec has an orientation (HORIZONTAL or VERTICAL), but no position (LEFT, RIGHT, TOP, BOTTOM), nor does it distinguish between Editor-level and View-level Toolbars.

Without a decision, the codebase has drifted:

- AreaWidget uses QTabWidget instead of QSplitter, consuming vertical space that scales poorly with 2x2 or 4x2 layouts.
- The Toolbar is rendered outside the Editor (on the left side of the Area), contradicting ADR-0002.
- Viewport3DEditor and MPRViewerEditor are named "Editors" but behave as views: they have no internal view layout, and the TomographyEditor that should host them does not exist.
- Toolbars for individual Views (e.g., the Axial View inside the TomographyEditor) cannot be declared or rendered, making the active/inactive state management required by the prototype impossible.

This ADR fills these three gaps. It does not change the core decisions of ADR-0001 or ADR-0002; it completes them by defining the boundaries between Editor-level and View-level Toolbars.

---

## 2. Decision

### 2.1 The four-level hierarchy

CranioZ organizes the UI in four nested levels:

```text
Workspace
└── Area Layout Tree (nested QSplitters)
    └── Area
        └── Editor Layout Tree (nested QSplitters or EditorStack)
            └── Editor
                ├── Editor Toolbar(s) (LEFT, RIGHT, TOP, BOTTOM)
                └── View Layout Tree (nested QSplitters)
                    └── View
                        ├── View Toolbar(s) (LEFT, RIGHT, TOP, BOTTOM)
                        └── View Control Panel(s) (LEFT, RIGHT, TOP, BOTTOM)

```
ach level has a single responsibility:

Level	Responsibility	Owned by
Area	Structural container. Occupies a position in the Area Layout Tree. Can be hidden (except Central). Hosts Editors.	Workspace
Editor	Functional unit. Hosts Views, Editor-level Toolbars, and Overlays. Coordinates the View Layout Tree.	EditorRegistry (type), Area (instance)
View	Visual representation of an aspect of the Scene (e.g., Axial, Coronal, Sagittal, 3D). Declares View-level Toolbars.	Editor (instance)
Toolbar	Presents Tools to the user. Materialized from a ToolbarSpec. May belong to the Editor or to a specific View.	Editor or View (declaration), Renderers (materialization)
2.2 Editor Layout Tree is rendered as nested QSplitters
The Editor Layout Tree is rendered as nested QSplitter widgets, the same way the Area Layout Tree is rendered.

A Leaf in the Editor Layout Tree is rendered as the Editor widget.

A Split is rendered as a QSplitter with the specified orientation (HORIZONTAL or VERTICAL).

The LayoutRenderer is the sole materializer of the tree, as with the Area Layout Tree.

Tabs are not the default organization. Tabs are an optional presentation mode for stacking multiple Editors in the same Leaf (see §2.5). The default organization is the split tree.

2.3 View is a first-class concept
A View is a visual representation of an aspect of the Scene, hosted by an Editor. Examples: AxialView, CoronalView, SagittalView, Viewport3DView, CurvedMPRView.

A View:

Has a stable view_id.

Has a view_type (e.g., "axial", "coronal", "sagittal", "3d", "curved_mpr").

Renders a content_widget().

Reads the Scene through SceneQuery (read-only).

Does not own the Scene, the Editor, or the Area.

Declares its own Toolbars and Control Panels via toolbar_specs() and control_panel_specs().

An Editor:

Hosts one or more Views.

Organizes its Views in a View Layout Tree (see §2.4).

Declares its own Editor-level Toolbars via toolbar_specs().

Distinction from ADR-0001: The ADR-0001 lists Viewport3D and MPR Viewer as Editors. This ADR clarifies: they are Views, not Editors. The TomographyEditor is the Editor; AxialView, CoronalView, SagittalView, and Viewport3DView are its Views. The CephalometryEditor hosts its own Views. This distinction is what allows a single Editor to host multiple simultaneous views (e.g., a 2x2 grid of Axial, Coronal, Sagittal, and 3D).

2.4 View Layout Tree
The View Layout Tree is the Editor's internal organization of its Views. It uses the same N-ary split tree model as the Area Layout Tree and the Editor Layout Tree.

A Leaf is rendered as the View's composite widget (which includes its Toolbars and Control Panels).

A Split is rendered as a QSplitter.

The Editor owns its View Layout Tree.

The View Layout Tree is internal to the Editor. The Area and the Workspace do not know about it.

2.5 Editor Stack (optional stacking)
When the user wants to stack multiple Editors in the same Leaf, the preferred presentation is an Editor Stack: a compact switcher that lets the user toggle between the stacked Editors. The Editor Stack can be horizontal (at the bottom of the Editor) or vertical (on the side).

The Editor Stack consumes minimal space.

The Editor Stack is not a QTabWidget.

The Editor Stack is a UI widget, materialized by the AreaLayoutRenderer (or by the AreaWidget).

The Editor Stack is optional.

2.6 Toolbar Placement and Visibility
CranioZ distinguishes between Editor-level Toolbars and View-level Toolbars. Both use the same ToolbarSpec contract, with both orientation and position.

python
class ToolbarOrientation(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

class ToolbarPosition(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"

class ToolbarVisibilityMode(Enum):
    ALWAYS = "always"
    COLLAPSIBLE = "collapsible"
    ACTIVE_ONLY = "active_only"  # New: Visible only when the owning View is active
    HIDDEN = "hidden"

@dataclass(frozen=True)
class ToolbarSpec:
    toolbar_id: str
    title: str
    orientation: ToolbarOrientation = ToolbarOrientation.HORIZONTAL
    position: ToolbarPosition = ToolbarPosition.TOP
    tool_ids: tuple[str, ...] = ()
    visibility_mode: ToolbarVisibilityMode = ToolbarVisibilityMode.ALWAYS
Placement rules:

Editor-level Toolbars: Rendered by the AreaLayoutRenderer (or LayoutRenderer) around the entire View Layout Tree of the Editor.

View-level Toolbars: Rendered by the ViewLayoutRenderer around the content_widget() of the specific View. A View may have multiple Toolbars (e.g., one LEFT with tools, one RIGHT with display controls).

View-level Control Panels: These are treated as a specialized form of View-level Toolbar (e.g., a RIGHT Toolbar dedicated to display settings like window/level, LUT, and visibility).

Visibility rules:

Active View: When a View becomes active within an Editor, its View-level Toolbars become visible (if their visibility_mode is ACTIVE_ONLY or ALWAYS). The Toolbars of inactive Views remain hidden to maximize the available screen real estate.

Editor-level Toolbars: These remain visible according to their own visibility_mode (usually ALWAYS or COLLAPSIBLE), regardless of which View is active, as they control Editor-wide behavior.

2.7 The Area does not own Toolbars
The Area does not render Toolbars. The Area does not know what Toolbars exist. Each Editor declares its own Editor-level Toolbars, and each View declares its own View-level Toolbars. The renderers materialize them inside the Editor's widget and the View's widget, respectively.

This preserves ADR-0002 §2.2: "Toolbars are internal to an Editor, not to an Area."

2.8 The prototype is illustrative, not normative
The prototype (Prototipagem_UI_17.pdf) shows tabs and Toolbars. These are illustrative, not normative:

The tabs are replaced by the split tree (§2.2) and the Editor Stack (§2.5).

The Toolbars are internal to the Editor and to the Views (§2.6).

Where the prototype conflicts with the ADRs, the ADRs win.

3. Rationale
3.1 The split tree scales, tabs do not
Tabs consume vertical (or horizontal) space. The split tree uses space proportionally. No space is lost to chrome.

3.2 Views are the right abstraction
A Viewport3D is not an Editor. It is a way to look at the Scene in 3D. An MPR Viewer is a way to look at the Scene in 2D. The TomographyEditor is the Editor: it coordinates the Views, manages its Editor-level Toolbars, and handles the user's interaction. The Views are its internal representations. Conflating Views and Editors makes it impossible to have multiple Views in the same Editor.

3.3 Toolbar placement and active states are a real need
The prototype shows Toolbars on the left and right of the Editor's content. For an Editor with multiple Views (e.g., a 2x2 grid), each View needs its own Toolbars to provide context-specific tools. Displaying all Toolbars simultaneously would consume too much space. The ACTIVE_ONLY visibility mode solves this by hiding the Toolbars of inactive Views, leaving the screen clean and focused on the active View, while still preserving the architecture that View Toolbars belong to their respective Views.

3.4 The hierarchy is the same at every level
The Area Layout Tree, the Editor Layout Tree, and the View Layout Tree are all the same N-ary split tree model. This uniformity allows the renderers to use the same logic at every level.

3.5 Consistency with ADR-0001 and ADR-0002
ADR-0001 establishes Area ≠ Editor. This ADR adds Editor ≠ View.

ADR-0002 establishes Toolbar is internal to Editor. This ADR specifies that Toolbars can be internal to the Editor or to the View, and specifies where they sit.

Both ADRs are completed by this one.

4. Consequences
4.1 Positive consequences
AreaWidget is refactored to use QSplitter instead of QTabWidget, freeing vertical space in the Central Area.

Toolbars are moved inside the Editor (and its Views), honoring ADR-0002.

Viewport3DView and MPRView replace Viewport3DEditor and MPRViewerEditor as Views.

ToolbarPosition and ToolbarVisibilityMode allow Editors and Views to declare left/right/top/bottom Toolbars that activate contextually, matching the prototype.

The Editor Stack provides stacking without consuming tab space.

Future Editors scale: any Editor can host multiple Views, organize them in a split tree, and declare Toolbars on any side.

4.2 Negative consequences
The current AreaWidget must be refactored (QTabWidget → QSplitter).

Viewport3DEditor and MPRViewerEditor must be renamed to Viewport3DView and MPRView.

ToolbarSpec.position and ToolbarSpec.visibility_mode (with ACTIVE_ONLY) must be added.

The View contract must gain toolbar_specs() and control_panel_specs() methods.

The ViewLayoutRenderer must be extended to materialize Toolbars around each View's content widget.

The AreaLayoutRenderer must be refactored to stop materializing Toolbars, delegating that to the ViewLayoutRenderer.

4.3 Neutral consequences
The View is a new concept in the domain. It is an internal abstraction of the Editor. The Workspace does not know about Views.

The Editor Stack is a UI widget, not a new domain concept.

5. Rules applied by this ADR
The Area Layout Tree, the Editor Layout Tree, and the View Layout Tree use the same N-ary split tree model.

The Editor Layout Tree is rendered as nested QSplitter widgets, not as QTabWidget.

A View is a visual representation of an aspect of the Scene, hosted by an Editor.

An Editor hosts one or more Views, organized in a View Layout Tree.

The View Layout Tree is internal to the Editor.

An Editor declares its Editor-level Toolbars via toolbar_specs().

A View declares its View-level Toolbars and Control Panels via toolbar_specs() and control_panel_specs().

Each ToolbarSpec declares both orientation and position.

View-level Toolbars are rendered by the ViewLayoutRenderer around the View's content widget.

Editor-level Toolbars are rendered by the AreaLayoutRenderer around the View Layout Tree.

ToolbarVisibilityMode.ACTIVE_ONLY ensures that View-level Toolbars are only visible when their owning View is active.

The Area does not render Toolbars.

The Editor Stack is the preferred presentation for stacking multiple Editors in the same Leaf.

Viewport3D and MPR Viewer are Views, not Editors.

6. Rejected alternatives
6.1 Keep tabs as the default organization
Rejected. Tabs consume space that scales poorly.

6.2 Keep Viewport3D and MPR Viewer as Editors
Rejected. They are views of the same underlying data.

6.3 Toolbar position as a ToolbarSpec field, but rendered by the Area
Rejected. The Area does not own Toolbars (ADR-0002).

6.4 All Toolbars belong to the Editor (no View-level Toolbars)
Rejected. An Editor with multiple Views (e.g., a 2x2 grid) needs context-specific tools for each View. Putting all tools in Editor-level Toolbars would either overcrowd the Toolbar or force the user to work with irrelevant tools. View-level Toolbars with ACTIVE_ONLY visibility solve this by showing the right tools at the right time.

6.5 Update the prototype first, then the ADRs
Rejected. The ADRs are normative; the prototype is illustrative.

7. Example
7.1 A TomographyEditor with four Views and View-level Toolbars
python
class TomographyEditor(Editor):
    editor_id = "editor.tomography"
    title = "Tomography"

    def __init__(self):
        super().__init__(editor_id=self.editor_id, title=self.title)
        self._axial = AxialView(view_id="view.axial")
        self._coronal = CoronalView(view_id="view.coronal")
        self._sagittal = SagittalView(view_id="view.sagittal")
        self._viewport = Viewport3DView(view_id="view.3d")

    def views(self) -> tuple[View, ...]:
        return (self._axial, self._coronal, self._sagittal, self._viewport)

    def view_layout(self) -> ViewLayoutSpec:
        return ViewLayoutSpec.split(
            SplitDirection.VERTICAL,
            (
                ViewLayoutSpec.split(
                    SplitDirection.HORIZONTAL,
                    (ViewLayoutSpec.leaf("view.axial"), ViewLayoutSpec.leaf("view.coronal")),
                ),
                ViewLayoutSpec.split(
                    SplitDirection.HORIZONTAL,
                    (ViewLayoutSpec.leaf("view.sagittal"), ViewLayoutSpec.leaf("view.3d")),
                ),
            ),
        )

    def toolbar_specs(self) -> list[ToolbarSpec]:
        # Editor-level Toolbar (none in this example, or a global visibility control)
        return []

class MPRView(View):
    def toolbar_specs(self) -> list[ToolbarSpec]:
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.view_id}.tools",
                title="Image Tools",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.LEFT,
                tool_ids=("tool.window_level", "tool.zoom", "tool.pan"),
                visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY,
            )
        ]

    def control_panel_specs(self) -> list[ToolbarSpec]:
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.view_id}.display",
                title="Display",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.RIGHT,
                tool_ids=("tool.lut", "tool.ruler", "tool.crosshair"),
                visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY,
            )
        ]
The rendered Editor when the Axial View is active:

text
┌─────────────────────────────────────────────────────────┐
│ Area Central                                            │
│ ┌──────────────────────┬──────────────────────────────┐ │
│ │ [Axial View]         │ [Coronal View]               │ │
│ │                      │                              │ │
│ │ [T] [Image] [T]      │ [Coronal]                    │ │
│ │     [Display]        │                              │ │
│ ├──────────────────────┼──────────────────────────────┤ │
│ │ [Sagittal View]      │ [3D View]                    │ │
│ │                      │                              │ │
│ │ [Sagittal]           │ [3D]                         │ │
│ └──────────────────────┴──────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
When the user clicks on the Coronal View, the Axial View's Toolbars are hidden (because ACTIVE_ONLY), and the Coronal View's Toolbars become visible.

8. Summary
This ADR completes ADR-0001 and ADR-0002 by filling three gaps:

Editor Layout Tree is rendered as nested QSplitters. Tabs are not the default. The Editor Stack is the preferred presentation for stacking.

View is a first-class concept. Viewport3D and MPR Viewer are Views. The TomographyEditor and CephalometryEditor are the Editors that host them.

Toolbar placement and visibility are explicit. Toolbars belong to the Editor or to the View. A View can declare its own Toolbars and Control Panels. ToolbarVisibilityMode.ACTIVE_ONLY ensures that View-specific Toolbars only consume screen space when their View is active.

The four-level hierarchy is:

text
Workspace → Area → Editor → View
Each level uses the same N-ary split tree model. Each level has a single responsibility. The Workspace remains ignorant of Views, Toolbars, and Editor behavior.