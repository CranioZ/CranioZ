ADR-0013: Editor Layout Tree, View Layout Tree, and Toolbar Placement
Status: Accepted
Date: 2026-10-30
Deciders: Architecture team
Related: ADR-0001_Area_and_Editor.md, ADR-0002_EditorContext_and_Toolbar_Materialization.md, editors.md, workspace.md, toolbar.md, tools.md

## 1. Context
ADR-0001 established that Area and Editor are distinct concepts: the Area is a structural container, and the Editor is a functional unit hosted inside it. The Area manages its Editors via an internal Editor Layout Tree, and there is no _EditorHost_.

ADR-0002 established that Toolbars are internal to an Editor, not to an Area, and that the LayoutRenderer materializes Toolbars from the Editor's _toolbar_specs()_.

Together, these two ADRs define the relationship Area → Editor → Toolbar. But they leave three gaps that have caused ambiguity in the codebase, in the prototype, and in the current AreaWidget implementation:

1. Editor Layout Tree rendering. The ADR-0001 defines the tree, but does not specify how it is rendered (nested QSplitter, QTabWidget, or something else). The current AreaWidget uses QTabWidget (tabs at the bottom of the Area). The ADR-0001 §2 says "each Split is rendered as a QSplitter", but the rationale (§3.1, §4.1) cites the prototype's tabs as evidence. This inconsistency has propagated into the code.
2. Editor vs. View. The ADR-0001 lists Viewport3D and MPR Viewer as examples of Editors. But the prototype shows them as views inside a larger Editor (e.g., the TomographyEditor hosts Axial, Coronal, Sagittal, and 3D views). The ADR-0001 does not define a "View" concept, and the codebase has no View abstraction. As a result, Viewport3DEditor and MPRViewerEditor are currently both Editors and views, which conflates two distinct concepts.
3. Toolbar placement. ADR-0002 says Toolbars are internal to an Editor, but does not specify where they sit inside the Editor. The prototype shows Toolbars on the left or right of the Editor's content (vertical), or on top (horizontal). The current ToolbarSpec has an orientation (HORIZONTAL or VERTICAL), but no position (LEFT, RIGHT, TOP, BOTTOM). This makes it impossible for the Editor to declare "this Toolbar goes on the right side" or "this Toolbar goes on the left side".

Without a decision, the codebase has drifted:

AreaWidget uses QTabWidget instead of QSplitter, consuming vertical space that scales poorly with 2x2 or 4x2 layouts.

The Toolbar is rendered outside the Editor (on the left side of the Area), contradicting ADR-0002.

Viewport3DEditor and MPRViewerEditor are named "Editors" but behave as views: they have no internal view layout, and the TomographyEditor that should host them does not exist.

This ADR fills the three gaps. It does not change the decisions of ADR-0001 or ADR-0002; it completes them.

## 2. Decision
2.1 The four-level hierarchy
CranioZ organizes the UI in four nested levels:


    Workspace
    └── Area Layout Tree (nested QSplitters)
        └── Area
            └── Editor Layout Tree (nested QSplitters)
                └── Editor
                    ├── Toolbar (LEFT, optional)
                    ├── View Layout Tree (nested QSplitters or EditorStack)
                    │   └── View (Axial, Coronal, Sagittal, 3D, ...)
                    ├── Toolbar (RIGHT, optional)
                    └── Overlays (internal)

Each level has a single responsibility:

    Level	                Responsibility	                                                                                                    Owned by
    Area	                Structural container. Occupies a position in the Area Layout Tree. Can be hidden (except Central). Hosts Editors.   Workspace
    Editor	                Functional unit. Hosts Views, Toolbars, and Overlays.	                                                            EditorRegistry (type), Area (instance)
    View	                Visual representation of an aspect of the Scene (e.g., Axial, Coronal, Sagittal, 3D).	                            Editor (instance)
    Toolbar	                Presents Tools to the user. Materialized from a ToolbarSpec.	                                                    Editor (declaration), LayoutRenderer (materialization)

### 2.2 Editor Layout Tree is rendered as nested QSplitters
The Editor Layout Tree is rendered as nested QSplitter widgets, the same way the Area Layout Tree is rendered.

A Leaf in the Editor Layout Tree is rendered as the Editor widget.

A Split is rendered as a QSplitter with the specified orientation (HORIZONTAL or VERTICAL).

The LayoutRenderer is the sole materializer of the tree, as with the Area Layout Tree.

Tabs are not the default organization. Tabs are an optional presentation mode for stacking multiple Editors in the same Leaf (see §2.5). The default organization is the split tree.

### 2.3 View is a first-class concept
A View is a visual representation of an aspect of the Scene, hosted by an Editor. Examples: AxialView, CoronalView, SagittalView, Viewport3DView, CurvedMPRView.

A View:

* Has a stable view_id.
* Has a view_type (e.g., "axial", "coronal", "sagittal", "3d", "curved_mpr").
* Renders a content_widget().
* Reads the Scene through SceneQuery (read-only).
* Does not own the Scene, the Editor, or the Area.

An Editor:

* Hosts one or more Views.
* Organizes its Views in a View Layout Tree (see §2.4).
* Declares its Toolbars via toolbar_specs().

Distinction from ADR-0001. The ADR-0001 lists Viewport3D and MPR Viewer as Editors. This ADR clarifies: they are Views, not Editors. The TomographyEditor is the Editor; AxialView, CoronalView, SagittalView, and Viewport3DView are its Views. Similarly, the CephalometryEditor hosts its own Views. This distinction is what allows a single Editor to host multiple simultaneous views (e.g., a 2x2 grid of Axial, Coronal, Sagittal, and 3D).

### 2.4 View Layout Tree
The View Layout Tree is the Editor's internal organization of its Views. It uses the same N-ary split tree model as the Area Layout Tree and the Editor Layout Tree.

* A Leaf is rendered as the View widget.
* A Split is rendered as a QSplitter.
* The Editor owns its View Layout Tree.

The View Layout Tree is internal to the Editor. The Area and the Workspace do not know about it. This preserves the Workspace's single rule (workspace.md §1.2): "The Workspace manages Areas and Overlays. It does not own clinical state, Tools, Toolbars, or Module behavior."

### 2.5 Editor Stack (optional stacking)
When the user wants to stack multiple Editors in the same Leaf (e.g., Viewport3DEditor and MPRViewerEditor sharing the same quadrant), the preferred presentation is an Editor Stack: a small switcher in the Editor's corner that lets the user toggle between the stacked Editors.

The Editor Stack consumes minimal space (a small icon or dropdown).

The Editor Stack is not a QTabWidget. Tabs consume vertical or horizontal space that scales poorly with 2x2 or 4x2 layouts.

The Editor Stack is a UI widget, not a new architectural concept. It is materialized by the LayoutRenderer (or by the AreaWidget) from the Editor's editor_stack metadata.

The Editor Stack is optional. If the user never stacks Editors, the split tree alone is sufficient.

### 2.6 Toolbar placement
A ToolbarSpec declares both orientation and position:


    class ToolbarOrientation(Enum):
        HORIZONTAL = "horizontal"
        VERTICAL = "vertical"
    
    class ToolbarPosition(Enum):
        TOP = "top"
        BOTTOM = "bottom"
        LEFT = "left"
        RIGHT = "right"
    
    @dataclass(frozen=True)
    class ToolbarSpec:
        toolbar_id: str
        title: str
        orientation: ToolbarOrientation = ToolbarOrientation.HORIZONTAL
        position: ToolbarPosition = ToolbarPosition.TOP
        tool_ids: tuple[str, ...] = ()
        visibility_mode: ToolbarVisibilityMode = ToolbarVisibilityMode.ALWAYS

The Editor materializes its Toolbars according to their position:

* LEFT / RIGHT: vertical Toolbar on the left or right of the View Layout Tree.
* TOP / BOTTOM: horizontal Toolbar above or below the View Layout Tree.

An Editor may declare multiple Toolbars with different positions. For example, the TomographyEditor may declare:

* A LEFT Toolbar with image tools (window/level, zoom, pan).
* A RIGHT Toolbar with visibility controls (mask visibility, volume visibility).

The LayoutRenderer materializes both, placing them on the correct side of the View Layout Tree.

### 2.7 The Area does not own Toolbars
The Area does not render Toolbars. The Area does not know what Toolbars exist. Each Editor declares its own Toolbars via toolbar_specs(), and the LayoutRenderer materializes them inside the Editor's widget.

This preserves ADR-0002 §2.2: "Toolbars are internal to an Editor, not to an Area."

### 2.8 The prototype is illustrative, not normative
The prototype (Prototipagem_UI_14.pdf) shows tabs at the bottom of each Area and Toolbars on the left of the Area. These are illustrative, not normative:

* The tabs are replaced by the split tree (§2.2) and the Editor Stack (§2.5).
* The Toolbars outside the Area are replaced by Toolbars inside the Editor (§2.6).

Where the prototype conflicts with the ADRs, the ADRs win. The prototype is updated to reflect the correct hierarchy.

## 3. Rationale
### 3.1 The split tree scales, tabs do not
Tabs consume vertical (or horizontal) space. In a 2x2 layout, each quadrant has ~300px of height; tabs consume ~30px (10%). In a 4x2 layout, each quadrant has ~150px; tabs consume ~30px (20%). At 8+ Editors, tabs are unworkable.

The split tree uses space proportionally: each Leaf occupies a fraction of the available space, and the user can resize the split. No space is lost to chrome.

### 3.2 Views are the right abstraction
A Viewport3D is not an Editor. It is a way to look at the Scene in 3D. An MPR Viewer is not an Editor. It is a way to look at the Scene in 2D (Axial, Coronal, Sagittal). They are views of the same underlying data.

The TomographyEditor is the Editor: it coordinates the Views, manages the Toolbars, and handles the user's interaction with the tomography data. The Views are its internal representations.

Conflating Views and Editors (as the current code does) makes it impossible to have multiple Views in the same Editor, which is exactly what the prototype (Page 54, Page 58) requires.

### 3.3 Toolbar placement is a real need
The prototype shows Toolbars on the left and right of the Editor's content. Without ToolbarPosition, the Editor cannot declare this. The current code assumes all Toolbars are on the top (HORIZONTAL) or on the left (VERTICAL), which is not what the prototype shows.

### 3.4 The hierarchy is the same at every level
The Area Layout Tree, the Editor Layout Tree, and the View Layout Tree are all the same N-ary split tree model:

* Leaf contains one element.
* Split contains two or more children and a direction.

This uniformity is not accidental. It is what allows the LayoutRenderer to render the Editor Layout Tree with the same logic it uses for the Area Layout Tree, and what allows the Editor to render its View Layout Tree with the same logic. One model, three levels.

### 3.5 Consistency with ADR-0001 and ADR-0002
* ADR-0001 establishes Area ≠ Editor. This ADR adds Editor ≠ View.
* ADR-0002 establishes Toolbar is internal to Editor. This ADR specifies where, inside the Editor, the Toolbar sits.
* Both ADRs are unchanged by this one. This ADR completes them.

## 4. Consequences
### 4.1 Positive consequences
* AreaWidget is refactored to use QSplitter instead of QTabWidget, freeing vertical space in the Central Area.
* Toolbar is moved inside the Editor, honoring ADR-0002.
* Viewport3DView and MPRView replace Viewport3DEditor and MPRViewerEditor as Views. The TomographyEditor and CephalometryEditor become real Editors that host these Views.
* ToolbarPosition allows Editors to declare left/right/top/bottom Toolbars, matching the prototype.
* The Editor Stack provides stacking without consuming tab space.
* The prototype is updated to reflect the correct hierarchy (no tabs, no Toolbars outside the Editor).
* Future Editors scale: any Editor can host multiple Views, organize them in a split tree, and declare its Toolbars on any side.

### .2 Negative consequences
* The current AreaWidget must be refactored (QTabWidget → QSplitter). This is a code change, not an ADR change.
* Viewport3DEditor and MPRViewerEditor must be renamed to Viewport3DView and MPRView, and their contracts updated. This is a rename, not a redesign.
* ToolbarSpec.position must be added to the existing ToolbarSpec dataclass, with a default of TOP to preserve backward compatibility with existing Toolbars.
* The Editor contract must gain a views() method and a view_layout() method. This is an extension, not a break.
* The prototype must be updated to reflect the new hierarchy. This is a documentation change.

### 4.3 Neutral consequences
* The View is a new concept in the domain. It is not a new architectural layer; it is an internal abstraction of the Editor. The Workspace does not know about Views.
* The Editor Stack is a UI widget, not a new domain concept. It is materialized by the LayoutRenderer (or by the AreaWidget) from the Editor's metadata.

## 5. Rules applied by this ADR
1. The Area Layout Tree, the Editor Layout Tree, and the View Layout Tree use the same N-ary split tree model.
2. The Editor Layout Tree is rendered as nested QSplitter widgets, not as QTabWidget.
3. A View is a visual representation of an aspect of the Scene, hosted by an Editor.
4. An Editor hosts one or more Views, organized in a View Layout Tree.
5. The View Layout Tree is internal to the Editor. The Area and the Workspace do not know about it.
6. An Editor declares its Toolbars via toolbar_specs().
7. Each ToolbarSpec declares both orientation and position.
8. The Toolbar is rendered inside the Editor, on the side specified by position.
9. The Area does not render Toolbars.
10. The Editor Stack is the preferred presentation for stacking multiple Editors in the same Leaf. Tabs are not.
11. The prototype is illustrative, not normative. Where it conflicts with the ADRs, the ADRs win.
12. Viewport3D and MPR Viewer are Views, not Editors. The TomographyEditor is the Editor that hosts them.

## 6. Rejected alternatives
### 6.1 Keep tabs as the default organization
Rejected. Tabs consume space that scales poorly with 2x2, 4x2, and 8+ layouts. The split tree is the correct organization.

### 6.2 Keep Viewport3D and MPR Viewer as Editors
Rejected. They are views of the same underlying data. Conflating them with Editors makes it impossible to host multiple views in the same Editor, which the prototype requires.

### 6.3 Toolbar position as a ToolbarSpec field, but rendered by the Area
Rejected. The Area does not own Toolbars (ADR-0002). The Editor owns them, and the LayoutRenderer materializes them inside the Editor.

### 6.4 No Editor Stack; rely on split tree only
Rejected. The split tree works well for side-by-side Editors. For stacked Editors (e.g., 3D + MPR in the same quadrant), a switcher is needed. The Editor Stack provides this without consuming tab space.

### 6.5 Update the prototype first, then the ADRs
Rejected. The ADRs are normative; the prototype is illustrative. The correct order is: write the ADR, then update the code, then update the prototype.

## 7. Example
### 7.1 A TomographyEditor with four Views and two Toolbars

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
                SplitDirection.HORIZONTAL,
                (
                    ViewLayoutSpec.leaf("view.axial"),
                    ViewLayoutSpec.split(
                        SplitDirection.VERTICAL,
                        (
                            ViewLayoutSpec.leaf("view.coronal"),
                            ViewLayoutSpec.split(
                                SplitDirection.HORIZONTAL,
                                (
                                    ViewLayoutSpec.leaf("view.sagittal"),
                                    ViewLayoutSpec.leaf("view.3d"),
                                ),
                            ),
                        ),
                    ),
                ),
            )
    
        def toolbar_specs(self) -> list[ToolbarSpec]:
            return [
                ToolbarSpec(
                    toolbar_id="toolbar.tomography.left",
                    title="Image Tools",
                    orientation=ToolbarOrientation.VERTICAL,
                    position=ToolbarPosition.LEFT,
                    tool_ids=("tool.window_level", "tool.zoom", "tool.pan"),
                ),
                ToolbarSpec(
                    toolbar_id="toolbar.tomography.right",
                    title="Visibility",
                    orientation=ToolbarOrientation.VERTICAL,
                    position=ToolbarPosition.RIGHT,
                    tool_ids=("tool.toggle_volume", "tool.toggle_mask"),
                ),
            ]
The rendered Editor:

    ┌─────────────────────────────────────────────────────────┐
    │ [Toolbar LEFT] [View Layout Tree] [Toolbar RIGHT]       │
    │                                                         │
    │  ┌───────────────┬─────────────────────────────────┐    │
    │  │               │                                 │    │
    │  │  Axial        │  Coronal                        │    │
    │  │               │                                 │    │
    │  │               ├─────────────────────────────────┤    │
    │  │               │                                 │    │
    │  │               │  Sagittal  │  3D                │    │
    │  │               │            │                    │    │
    │  └───────────────┴────────────┴────────────────────┘    │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
### 7.2 An Area hosting a single Editor

    area = Area(area_id="area.central", title="Central", placement=Placement.CENTRAL)
    area.add_editor(TomographyEditor())

The rendered Area:

    ┌─────────────────────────────────────────────────────────┐
    │ Area Central                                            │
    │ ┌─────────────────────────────────────────────────────┐ │
    │ │ [TomographyEditor]                                  │ │
    │ │                                                     │ │
    │ │  [Toolbar LEFT] [View Layout Tree] [Toolbar RIGHT]  │ │
    │ │                                                     │ │
    │ └─────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────┘

### 7.3 An Area hosting multiple Editors (split tree, not tabs)

    area = Area(area_id="area.central", title="Central", placement=Placement.CENTRAL)
    area.add_editor(TomographyEditor())
    area.add_editor(CephalometryEditor())
    area.set_editor_layout(
        EditorLayoutSpec.split(
            SplitDirection.HORIZONTAL,
            (
                EditorLayoutSpec.leaf("editor.tomography"),
                EditorLayoutSpec.leaf("editor.cephalometry"),
            ),
        )
    )

The rendered Area:

    ┌─────────────────────────────────────────────────────────┐
    │ Area Central                                            │
    │ ┌──────────────────────┬──────────────────────────────┐ │
    │ │ [TomographyEditor]   │ [CephalometryEditor]         │ │
    │ │                      │                              │ │
    │ │  [T] [Views] [T]     │  [T] [Views] [T]             │ │
    │ │                      │                              │ │
    │ └──────────────────────┴──────────────────────────────┘ │
    └─────────────────────────────────────────────────────────┘
No tabs. Each Editor occupies its full Leaf in the split tree. The Toolbars are inside each Editor.

### 7.4 An Editor Stack for stacked Editors
If the user wants to stack TomographyEditor and CephalometryEditor in the same Leaf (e.g., to alternate between them without resizing):


    area.set_editor_stack(
        editor_ids=("editor.tomography", "editor.cephalometry"),
    )
The rendered Area:

    ┌─────────────────────────────────────────────────────────┐
    │ Area Central                                            │
    │ ┌─────────────────────────────────────────────────────┐ │
    │ │ [▼ Switcher]  [TomographyEditor]                    │ │
    │ │                                                     │ │
    │ │  [Toolbar LEFT] [View Layout Tree] [Toolbar RIGHT]  │ │
    │ │                                                     │ │
    │ └─────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────┘
The user clicks the switcher (▼) to toggle between TomographyEditor and CephalometryEditor. No tabs, minimal space.

## 8. Summary
This ADR completes ADR-0001 and ADR-0002 by filling three gaps:

Editor Layout Tree is rendered as nested QSplitters. Tabs are not the default. The Editor Stack is the preferred presentation for stacking.

View is a first-class concept. Viewport3D and MPR Viewer are Views, not Editors. The TomographyEditor and CephalometryEditor are the Editors that host them.

Toolbar placement is explicit. ToolbarSpec gains a position field (LEFT, RIGHT, TOP, BOTTOM). Toolbars are rendered inside the Editor, on the correct side.

The four-level hierarchy is:


    Workspace → Area → Editor → View
    Each level uses the same N-ary split tree model. Each level has a single responsibility. The Workspace remains ignorant of Views, Toolbars, and Editor behavior.

The prototype is illustrative, not normative. Where it conflicts with the ADRs, the ADRs win. The prototype is updated to reflect the correct hierarchy.

This ADR is the foundation for the Phase 4 refactoring: the AreaWidget will use QSplitter instead of QTabWidget, the Viewport3DEditor and MPRViewerEditor will be renamed to Viewport3DView and MPRView, and the TomographyEditor will be introduced as the Editor that hosts them.