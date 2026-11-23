# Widget Catalog

**Document type:** UI component catalog  
**Status:** Draft  
**Version:** 0.4
**Scope:** Reusable UI widgets and components available or planned for CranioZ  
**Last updated:** 2026-11-23

---

## 1. Purpose

This document defines the catalog of reusable UI widgets and components for CranioZ.

It serves as the reference for:

- identifying reusable UI components;
- defining component ownership and architectural boundaries;
- documenting implementation status and planned milestones;
- recording dependencies on Qt components and other system widgets;
- preventing duplicated or unnecessary abstractions;
- guiding widget implementation and testing.

The catalog is a system-wide inventory. It does not imply that every listed component must be implemented immediately.

Implementation priorities are defined by the development plan and the corresponding sprint documents.

## 2. Terminology

The following terms are used throughout this document.

| Term | Definition |
|---|---|
| **Widget** | A visual UI component implemented using Qt Widgets or a custom QWidget subclass. |
| **Composite Widget** | A widget assembled from multiple Qt components or other widgets to provide a reusable higher-level interface. |
| **Qt Component** | A native Qt widget or a lightly customized native component that does not justify an independent custom abstraction. |
| **Editor** | A functional UI unit hosted by an Area. Editors compose widgets and provide application-specific interaction. |
| **Tool** | An actionable application operation declared by an Editor and presented through its Toolbar. |
| **Toolbar** | A presentation region inside an Editor that displays Tools. It is not a generic widget category. |
| **Module** | A declarative application unit that contributes functionality and UI configuration. A Module does not own reusable system widgets. |

A widget may be consumed by multiple Editors or Modules. Its implementation belongs to the system UI layer, not to the first consumer that requires it.

## 3. Classification and metadata

### 3.1 Implementation classification

Each catalog entry has one primary implementation classification.

| Classification | Meaning |
|---|---|
| **Custom Widget** | A dedicated widget with its own behavior, API, or rendering logic. |
| **Composite Widget** | A reusable composition of multiple components with a defined public interface. |
| **Qt Component** | A native Qt component used directly or with styling and minor configuration. |

A component must not receive multiple classifications. If a component is composed of other widgets, its primary classification is determined by its public role and implementation responsibility.

### 3.2 Status

`Status` describes the current implementation state.

| Status | Meaning |
|---|---|
| **Existing** | An implementation already exists in the CranioZ codebase. |
| **Planned** | The component has been identified and is intended for implementation. |
| **Backlog** | The component is recognized but has no committed implementation milestone. |

### 3.3 Milestone

`Milestone` identifies the planned implementation or delivery stage.

Examples:

- `L.0` — System form widgets.
- `L.1` — Professional profile Editor.
- `L.2` — Professional navigation and sections.
- `L.3+` — Future functionality.

A milestone does not describe implementation status. A component can be `Planned` for `L.2`, for example.

Components without a committed implementation stage are marked `TBD`.

## 4. Architectural boundaries

### 4.1 System widget ownership

Reusable widgets belong to:

`src/cranioz/ui/widgets/`

They must not be implemented inside a specific Module or Editor merely because that component is their first consumer.

Editors and Modules consume system widgets through their public APIs.

### 4.2 Editor-specific composition

An Editor may compose multiple system widgets into a higher-level interface.

For example, the ProfessionalEditor may use:

- FormField;
- FormCombo;
- FilePicker;
- SignaturePreview;
- IconSidebar;
- CollapsibleSection;
- DragList.

The Editor-specific compositions, such as `ProfessionalSidebar`, `ProfessionalSectionTree`, and `ProfessionalConfigPanel`, are not automatically system widgets. They should remain in the Professional Editor implementation unless there is a demonstrated need for reuse.

### 4.3 Toolbars and Tools

Toolbars are internal presentation regions of Editors. They receive Tools declared by the corresponding Editor.

The vertical toolbars and visibility-control regions shown in the UI prototypes are therefore not included as generic widgets in this catalog.

Their implementation and composition belong to the Editor and Toolbar architecture.

### 4.4 Main window controls

Application window controls, such as maximize, restore, and close, belong to the MainWindow implementation.

They are not reusable system widgets and are excluded from this catalog.

## 5. Widget catalog

The following sections are the authoritative ownership locations for each catalog entry. A component referenced elsewhere must not be listed again as an independent catalog entry.

### 5.1 Buttons and actions

Components representing discrete actions or commands.

| Component | Classification | Status | Milestone | Notes |
|---|---|---|---|---|
| OpenFolderButton | Qt Component | Existing | — | Uses an icon button or styled QPushButton to open a folder or file dialog. |
| AddObjectButton | Qt Component | Planned | TBD | Requests the addition of an object, volume, photograph, or other supported item. |
| AddModuleButton | Qt Component | Planned | TBD | Requests the addition of a Module, Area, or other supported application element. |
| StartButton | Qt Component | Planned | TBD | Starts a workflow or operation. |
| ContinueButton | Qt Component | Planned | TBD | Advances a workflow or confirms continuation. |
| CompleteButton | Qt Component | Planned | TBD | Marks an operation or workflow as completed. |
| PreviousButton | Qt Component | Planned | TBD | Navigates to the previous step. |
| NextButton | Qt Component | Planned | TBD | Navigates to the next step. |
| RemoveButton | Qt Component | Planned | TBD | Requests removal of a selected element. |
| SettingsButton | Qt Component | Planned | TBD | Opens a settings interface. |
| SearchField | Composite Widget | Existing | L.0.2 | Search input with an optional clear or search action. |
| BlurToggle | Qt Component | Planned | TBD | Toggles the background blur behavior where supported. |

**Implementation notes**

- Prefer QPushButton and QToolButton when their native behavior is sufficient.
- Existing button styling should be reused.
- Do not create a dedicated class for every button label or action.
- `OpenFolderButton` may remain a small reusable button component or an internal component of FilePicker. A separate class is justified only if it has independent reuse.
- `PreviousButton` and `NextButton` may share a common implementation or styling without requiring a new abstraction.
- Application window controls are excluded and remain the responsibility of MainWindow.

### 5.2 Forms and data entry

Reusable components for structured data entry and file selection.

| Component | Classification | Status | Milestone | Notes |
|---|---|---|---|---|
| FormField | Composite Widget | Existing | L.0 | Label and QLineEdit composition. |
| FormCombo | Composite Widget | Existing | L.0 | Label and QComboBox composition. |
| FilePicker | Composite Widget | Existing | L.0 | File or directory selection with a read-only path field and browse action. |
| SignaturePreview | Custom Widget | Existing | L.0 | Displays a signature image or an empty preview state. |
| DateField | Qt Component | Existing | L.0.2 | Uses QDateEdit with appropriate formatting and validation. |
| FormRow | Composite Widget | Existing | L.0.2 | Horizontal two-column form container. |

**Implementation notes**

FormField and FormCombo must expose a high-level public API. Consumers should not need to access their internal QLabel or input widget to perform ordinary operations.

Expected API responsibilities include:

- reading the current value;
- setting the current value;
- configuring the label;
- enabling or disabling the component;
- exposing relevant value-change signals.

An optional controlled accessor to the internal editor may be provided when a legitimate advanced use case requires it. It must not be the primary integration mechanism.

FilePicker should expose the selected path and a signal indicating that a selection has been made. Its internal browse button does not need to be a separately exported widget unless independent reuse is demonstrated.

SignaturePreview requires a defined contract for:

- supported input types;
- empty state;
- image or signature rendering;
- clearing or replacing the preview;
- size and aspect-ratio behavior.

DateField should use QDateEdit rather than wrapping QComboBox.

### 5.3 Sections and containers

Components that organize content into reusable visual sections.

| Component | Classification | Status | Milestone | Notes |
|---|---|---|---|---|
| CollapsibleSection | Composite Widget | Existing | L.0.2 | Header with expand/collapse behavior and a content area. |
| SectionHeader | Composite Widget | Backlog | TBD | Reserved file exists but has no implementation; CollapsibleSection currently owns its internal header. |
| CardContainer | Qt Component | Existing | — | Uses the existing QFrame/QSS card styling. |

**Implementation notes**

CollapsibleSection should provide:

- a clickable header;
- expanded and collapsed states;
- a content widget or layout;
- a signal for expansion-state changes;
- predictable keyboard interaction.

The component should not assume that it belongs to the Professional Editor. It must remain reusable by other Editors.

CardContainer does not require a dedicated class if the existing QFrame and QSS `card` styling provide the required behavior.

### 5.4 Navigation and configuration

Components used to navigate between sections or configure their presentation.

| Component | Classification | Status | Milestone | Notes |
|---|---|---|---|---|
| IconSidebar | Composite Widget | Existing | L.0.2 | Vertical navigation component with selectable icon items. |
| EyeToggleButton | Qt Component | Existing | L.0.2 | Toggles the visibility of an item or section. |
| DragHandle | Qt Component | Existing | L.0.2 | Visual handle indicating that an item can be reordered. |
| DragList | Custom Widget | Existing | L.0.2 | List supporting item reordering through drag-and-drop. |

**Implementation notes**

IconSidebar should expose a public API for registering or configuring navigation items and notifying the consumer when the active item changes.

It must not contain Professional-specific section definitions.

EyeToggleButton should expose its checked/visibility state and a corresponding signal. The visual state must not rely exclusively on color.

DragHandle is a small visual and interaction affordance. It should not become a general-purpose drag-and-drop framework.

DragList is a custom `QWidget` because its children are complex
`CollapsibleSection` widgets, not plain text rows. Sections are identified by
stable string keys. The public contract is `add_section(key, section)`,
`remove_section(key)`, `move_section(key, new_index)`, and `set_order(keys)`.
`order_changed(list[str])` reports the current key order; `section_added(str)`
and `section_removed(str)` report membership changes.

The following components are consumer-specific compositions and are not independent system widgets:

- ProfessionalSidebar;
- ProfessionalSectionTree;
- ProfessionalConfigPanel.

They belong to the Professional Editor implementation and may consume the system widgets listed above.

### 5.5 Interactive controls

Controls representing selection, activation, movement, or visibility states.

| Component | Classification | Status | Milestone | Notes |
|---|---|---|---|---|
| CheckBox | Qt Component | Planned | TBD | Native QCheckBox with CranioZ styling. |
| RadioButton | Qt Component | Planned | TBD | Native QRadioButton with CranioZ styling. |
| ObjectMovementControl | Custom Widget | Backlog | TBD | Interactive control for object movement. |
| VisibilityToggle | Qt Component | Existing | L.0.2 | Generic visibility state control when EyeToggleButton is not the appropriate semantic component. |

**Implementation notes**

CheckBox and RadioButton should use native Qt components unless a specific interaction requirement justifies a custom widget.

ObjectMovementControl requires a separate interaction specification before implementation. Its visual representation and movement semantics must be defined by the consuming Editor.

VisibilityToggle and EyeToggleButton must not become competing implementations
of the same behavior. EyeToggleButton is the icon-based control intended for the
Professional configuration interface. VisibilityToggle is the generic labeled
checkbox form used when an icon-only control is not appropriate.

### 5.6 Horizontal widgets

Independent horizontal components used for animation, measurement, or timeline interaction. These are not Toolbars.

| Component | Classification | Status | Milestone | Notes |
|---|---|---|---|---|
| TimelineSlider | Custom Widget | Planned | L.0.2 | Horizontal timeline control for animation playback and navigation. |

**Implementation notes**

TimelineSlider is intended for future animation or simulation workflows. Its specification must define frame range, current position, navigation, and synchronization with the corresponding animation state.

Ruler is not a system widget. It is reclassified as an Editor overlay under
`src/cranioz/ui/editors/overlays/rulers/`, following ADR-0003 §2.2. The overlay
is created with its first consuming Editor, not in the generic widget catalog.

Neither component should be implemented as a generic Toolbar.

### 5.7 Advanced widgets

Components with specialized visualization or interaction behavior.

| Component | Classification | Status | Milestone | Notes |
|---|---|---|---|---|
| ColorPicker | Composite Widget | Planned | L.0.2 | Color selection interface. |
| Histogram | Custom Widget | Planned | L.0.2 | Data distribution visualization. |
| ProgressBar | Qt Component | Existing | L.0.2 | Progress feedback for asynchronous operations. |

**Implementation notes**

ColorPicker should use native Qt color-selection capabilities where possible. A custom presentation may be added if the application requires a specific visual or interaction model.

Histogram is a data visualization component. Its implementation must define the input data contract, binning behavior, axes, and interaction requirements.

ProgressBar should use QProgressBar unless a specific requirement justifies a custom implementation.

Its integration with asynchronous operations depends on the TaskManager and TaskExecutor infrastructure. It must not introduce a separate task-management mechanism.

### 5.8 Sliders and range controls

Components used to select scalar values, ranges, or positions within an interval.

| Component | Classification | Status | Milestone | Notes |
|---|---|---|---|---|
| SingleSlider | Qt Component | Existing | — | Existing labeled slider implementation. |
| DualRangeSlider | Custom Widget | Planned | TBD — Tomography Editor | Selects a minimum and maximum value. |
| ScrollBar | Qt Component | Existing | — | Uses native QScrollBar. |
| SliceControl | Composite Widget | Planned | TBD — Tomography Editor | Controls the selected 2D tomographic slice. |
| LandmarkSizeControl | Composite Widget | Planned | TBD — Cephalometry Editor | Controls the display size of cephalometric landmarks. |
| SecondaryLandmarkSizeControl | Composite Widget | Backlog | TBD — Cephalometry Editor | Controls the display size of secondary landmarks if a distinct configuration is required. |

**Implementation notes**

SingleSlider is a Qt Component. The existing `labeled_slider.py` implementation should be retained and cataloged as SingleSlider rather than introducing a second slider abstraction.

DualRangeSlider requires two independently configurable values and a defined minimum/maximum relationship. It is intended for future tomography workflows.

SliceControl is a higher-level control that may combine a slider, labels, and navigation actions. It should use native Qt components where possible.

LandmarkSizeControl should use the existing SingleSlider where its behavior is sufficient. A separate custom slider implementation is not required.

SecondaryLandmarkSizeControl should remain a separate configuration only if it has an independent value or behavior. Otherwise, it should be represented as another instance of the same reusable control.

## 6. Dependency reference

This section records the principal implementation dependencies. Dependencies describe composition or implementation relationships; they do not necessarily require separate public widget classes.

| Component | Principal dependencies |
|---|---|
| FormField | QLabel + QLineEdit |
| FormCombo | QLabel + QComboBox |
| FilePicker | FormField or equivalent path display + browse button |
| SignaturePreview | QWidget or QFrame + preview rendering |
| DateField | QDateEdit |
| CollapsibleSection | QFrame + header + content widget/layout |
| IconSidebar | Icon buttons + layout + selection state |
| EyeToggleButton | QToolButton or QPushButton |
| DragHandle | QToolButton or custom-painted handle |
| DragList | QWidget + QVBoxLayout + QDrag/QDrop events |
| SearchField | QLineEdit + optional action button |
| SingleSlider | QSlider + optional label |
| DualRangeSlider | Custom range interaction and value presentation |
| SliceControl | Slider + labels + navigation controls |
| LandmarkSizeControl | SingleSlider + value presentation |
| TimelineSlider | Custom timeline interaction and scale |
| ColorPicker | Native color dialog or custom color-selection controls |
| Histogram | Custom data visualization |
| ProgressBar | QProgressBar |

## 7. Package structure

The package structure should reflect component responsibility and ownership.

```text
src/cranioz/ui/widgets/
├── __init__.py
├── buttons/
│   ├── __init__.py
│   ├── icon_button.py
│   └── primary_button.py
├── headers/
│   ├── __init__.py
│   └── section_header.py
├── forms/
│   ├── __init__.py
│   ├── form_field.py
│   ├── form_combo.py
│   ├── file_picker.py
│   ├── signature_preview.py
│   └── date_field.py
├── sections/
│   ├── __init__.py
│   └── collapsible_section.py
├── navigation/
│   ├── __init__.py
│   ├── icon_sidebar.py
│   └── eye_toggle_button.py
├── lists/
│   ├── __init__.py
│   ├── drag_handle.py
│   └── drag_list.py
├── sliders/
│   ├── __init__.py
│   └── labeled_slider.py
├── horizontal/
│   ├── __init__.py
│   ├── timeline_slider.py
│   └── ruler.py
└── advanced/
    ├── __init__.py
    ├── color_picker.py
    ├── histogram.py
    └── progress_bar.py
```

This is a target organization, not a requirement to create every directory immediately.

Directories should be created when they receive their first implementation. Every Python package directory must contain an `__init__.py` file.

The existing `icon_button.py`, `primary_button.py`, `section_header.py`, and `labeled_slider.py` must be preserved and correctly represented in the catalog.

`AppWindowControls` and other MainWindow-specific controls must remain outside this package.

## 8. Implementation guidelines

### 8.1 Qt-native components first

Prefer native Qt Widgets when they already provide the required behavior.

Create a custom widget only when at least one of the following applies:

- the required interaction is not adequately supported by native Qt components;
- the component has a reusable public API beyond simple composition;
- custom rendering or behavior is an essential part of the component;
- reuse across multiple Editors justifies a dedicated abstraction.

Avoid creating classes that only rename a native Qt widget without adding meaningful behavior or a stable public interface.

### 8.2 Public API and encapsulation

Composite widgets must expose the operations required by their consumers through a stable public API.

Consumers should not need to manipulate internal child widgets directly for ordinary tasks.

Internal implementation details should remain encapsulated unless a controlled accessor is justified by a real use case.

### 8.3 Internationalization

Use Qt's native translation mechanism.

- Widget-owned static text should use `self.tr()`.
- Widgets with internal text must update that text when receiving `QEvent.LanguageChange`.
- Text supplied by consumers should be provided through public properties, setters, or constructor arguments.
- Do not inject a `translate: Callable` into every widget.
- Do not introduce direct dependencies on TranslationService in reusable widgets.

### 8.4 Theme integration

ThemeManager and ThemeCompiler apply the application's global QSS and design tokens.

Widgets should not receive ThemeService as a constructor dependency by default.

For widgets using custom painting or deriving colors and metrics outside QSS:

- obtain the required values through the established design-token/theme mechanism;
- update derived visual values when the theme changes;
- trigger repainting when necessary;
- avoid hardcoded interface colors and dimensions.

QSS alone is not sufficient for custom-painted components whose rendering depends on theme values.

### 8.5 Accessibility

Widgets must support accessible interaction and predictable behavior.

Requirements include:

- meaningful `accessibleName` and `accessibleDescription` where appropriate;
- predictable keyboard focus order;
- keyboard interaction for selectable and actionable controls;
- visible focus indication;
- states that are not communicated exclusively through color;
- adequate contrast, targeting WCAG 2.2 AA where applicable.

### 8.6 HiDPI and scaling

All widget dimensions, margins, coordinates, and rendering metrics must respect Qt's device-independent scaling behavior.

Avoid manually multiplying dimensions by device pixel ratio when Qt already handles the scaling.

### 8.7 Clinical visualization colors

Clinical data visualization colors must be treated separately from general application theme colors.

Color mappings used to represent clinical structures, measurements, segmentation classes, or other data semantics must remain consistent with the visualization specification and must not change arbitrarily with the application theme.

## 9. Testing requirements

Tests should verify public behavior and component contracts rather than implementation details.

Where applicable, widget tests should cover:

- construction and default state;
- public properties and setters;
- emitted signals;
- user interaction;
- enabled and disabled states;
- keyboard behavior;
- translation updates;
- theme updates;
- accessibility-relevant properties;
- layout behavior under different sizes.

Tests belong under:

```text
tests/unit/ui/widgets/
```

Integration tests should be added when a widget interacts with an Editor or another application subsystem.

A widget should not be considered complete merely because it renders without errors.

## 10. Implementation priorities

The catalog contains components with different implementation priorities. The following table records the current planned scope.

| Milestone | Scope | Main components |
|---|---|---|
| **L.0** | System form widgets | FormField, FormCombo, FilePicker, SignaturePreview — **Complete (2026-11-23)** |
| **L.0.2** | Extended widget suite | DateField, FormRow, DragHandle, EyeToggleButton, VisibilityToggle, SearchField, ProgressBar, CollapsibleSection, DragList, IconSidebar — **Existing**; TimelineSlider, ColorPicker and Histogram pending |
| **L.1** | Professional profile Editor | Consumes L.0 widgets; does not introduce a separate widget-building milestone |
| **L.2** | Professional navigation and sections | Consumes L.0.2 navigation and section widgets |
| **L.3+** | Future functionality | Components whose dependencies and use cases become available |
| **TBD** | Future system-widget requirements | DualRangeSlider, SliceControl and other backlog components |

L.1 is a consumer milestone, not a widget implementation milestone. The ProfessionalEditor is an Editor hosted by the central Area and consumes reusable system widgets.

The catalog does not redefine Sprint L scope or the overall implementation plan. Those documents remain authoritative for execution sequencing and delivery criteria.

## 11. Explicit exclusions

The following elements are not cataloged as reusable system widgets:

- Editor Toolbars;
- individual Tools and their application-specific actions;
- MainWindow controls;
- ProfessionalSidebar, ProfessionalSectionTree, and ProfessionalConfigPanel as Professional-specific compositions;
- generic card containers that can be implemented with existing QFrame and QSS styling;
- duplicate button classes that only differ by text or icon;
- internal child widgets that do not have independent reuse or a meaningful public API.

These exclusions prevent the catalog from becoming a list of every visual element in the application.

## 12. Maintenance rules

This document should be updated whenever:

- a new reusable system widget is identified;
- an existing widget changes ownership or classification;
- an implementation status changes;
- a milestone is assigned or revised;
- a component is deprecated or removed;
- a dependency or architectural boundary changes.

Each component must have exactly one authoritative catalog entry.

When a component is referenced in another section, the reference must not create a second independent entry.

Status and milestone must remain separate fields.

The catalog should describe reusable system components, not reproduce the implementation plan or the complete UI hierarchy of individual Editors.
