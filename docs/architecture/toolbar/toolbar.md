Toolbar
## 1. Overview
A Toolbar is a graphical interface element responsible for providing a set of quick-access actions to the user.

In CranioZ, the Toolbar acts as a presentation interface for Tools, allowing frequently used operations to be executed directly from the interface.

The Toolbar does not implement the logic of the operations it presents. It only presents the interaction elements and forwards the user's action to the Tool, Command, or another appropriate mechanism.

This separation keeps the interface decoupled from domain logic and allows the same operation to be made available in different parts of the interface.

text
Toolbar
   │
   ├── Tool Button
   ├── Tool Button
   ├── Separator
   ├── Tool Button
   └── Tool Button
          │
          ▼
        Tool
          │
          ▼
       Command
          │
          ▼
     Application
          │
          ▼
        Domain
## 2. Role of the Toolbar
The Toolbar exists primarily to provide quick access to operations relevant to the current context.

It can present:

Tools;

frequently used commands;

navigation actions;

view controls;

actions specific to an Editor;

actions provided by modules;

actions provided by plugins.

The Toolbar must not be used as a place to implement clinical rules, business rules, or data processing.

Those responsibilities belong to the corresponding layers of the application.

## 3. Toolbar and Tool
A Tool represents an operational action that can be made available to the user. The Toolbar represents one of the possible ways to present that Tool in the interface.

Therefore, a Tool does not necessarily belong to a specific Toolbar. Depending on the context, the same Tool can be made available in:

a Toolbar;

a menu;

a context menu;

a panel;

a keyboard shortcut;

another interface component.

text
                 ┌── Toolbar
                 │
Tool ────────────┼── Menu
                 │
                 ├── Context Menu
                 │
                 └── Keyboard Shortcut
This relationship prevents the definition of the operation from becoming coupled to the visual component used to execute it.

## 4. Toolbar and Editor
CranioZ Toolbars are often associated with an Editor.

An Editor declares which Tools it needs to perform its function. The Toolbar uses that definition to make the corresponding Tools available to the user.

For example, a 3D visualization Editor may use:

text
[ Select ] [ Move ] [ Rotate ] [ Measure ] | [ View ] [ Reset ]
While a tomography Editor may use:

text
[ Window/Level ] [ Zoom ] [ Pan ] [ Crosshair ] | [ MPR ] [ Reset ]
The Toolbar, however, remains an interface component. The implementation of the operations stays in the respective Tools, Commands, or services.

The relationship can be represented as:

text
Tool Registry
      │
      ▼
   Editor
      │
      │ declares the Tools it uses
      ▼
   Toolbar
      │
      │ presents the Tools
      ▼
    User
## 5. Toolbar and Context
A Toolbar can be contextual. This means its content can change according to:

the active Editor;

the selected object;

the interaction mode;

the active module;

the current Flow;

the Workspace state;

the available capabilities.

For example, when an osteotomy is selected, certain Tools related to bone planning may become available.

When no compatible object is selected, those Tools may remain hidden or disabled.

The Toolbar must reflect the current operational context without taking responsibility for determining that context.

## 6. Action State
The elements presented by a Toolbar must reflect the current state of the application.

An action can be:

available;

unavailable;

disabled;

selected;

activated;

checked;

hidden.

For example:

text
[ Select ] [ Move ] [ Rotate ] [ Measure ]
    ✓
or:

text
[ Select ] [ Move ] [ Rotate ] [ Measure ]
                     ─────────
                     disabled
The determination of action availability must be based on the application's capabilities and conditions, not on rules implemented directly in the Toolbar.

## 7. Toolbar Items
The individual elements of a Toolbar are called Toolbar Items.

A Toolbar Item can represent an action or a visual organization element.

The main types include:

7.1 Action Item
Represents an executable action.

text
[ Select ]
It is usually associated with a Tool or Command.

7.2 Toggle Item
Represents an action that has an on/off state.

text
[ Grid ✓ ]
The visual state must reflect the real state of the functionality.

7.3 Separator
Separates functionally distinct groups of actions.

text
[ Select ] [ Move ] [ Rotate ] | [ Measure ] [ Angle ]
Separators should be used sparingly, mainly to establish semantic groupings.

7.4 Menu Item
Provides access to a set of related actions.

text
[ Transform ▼ ]
It can be used when directly presenting all actions would take up excessive space.

## 8. Organization of Tools
The Tools presented in a Toolbar should be grouped according to their function.

For example:

text
[ Select ] [ Move ] [ Rotate ]
                     |
                     ├── Manipulation

[ Measure ] [ Angle ] [ Distance ]
                     |
                     ├── Measurement

[ Reset ] [ Fit ]
                     |
                     └── View
The organization should prioritize:

frequency of use;

functional proximity;

clinical context;

Editor context;

consistency across different modules.

The Toolbar must not simply reproduce the complete list of available Tools.

It should present the operations relevant to the current context.

## 9. Toolbar and Modules
Modules can provide functionalities that are represented by Tools and later used by Editors and Toolbars.

The Tools, however, do not necessarily belong to the internal structure of a module. CranioZ maintains a common set of Tools available for use by the different components of the application.

For example, functionalities related to osteotomy may provide Tools such as:

text
[ Create Osteotomy ]
[ Edit Osteotomy ]
[ Preview ]
[ Apply ]
An Editor that works with osteotomy planning can declare these Tools among the ones it uses.

text
Module
   │
   │ provides functionality
   ▼
Tool
   │
   │ available in the system
   ▼
Editor
   │
   │ declares usage
   ▼
Toolbar
This separation allows the functionality provided by a module to be used by different Editors without coupling the Tool to a specific Toolbar.

## 10. Toolbar and Plugins
Plugins can provide additional functionalities that are made available through Tools.

These Tools can be registered in the system and later used by the Editors that need them.

Conceptually:

text
Core ────────────┐
                 │
Modules ─────────┼──► Tools ───► Editors ───► Toolbars
                 │
Plugins ─────────┘
A plugin must not depend on the internal implementation of a specific Toolbar.

Integration must occur through the public interfaces of the framework.

11. Main Toolbar and Contextual Toolbars
CranioZ can have different levels of Toolbar.

11.1 Main Toolbar
A Toolbar associated with the application or the main Workspace.

It can contain general-purpose operations, such as:

opening and saving projects;

undo and redo;

selection;

navigation;

general view operations.

11.2 Editor Toolbar
A Toolbar associated with a specific Editor.

It contains the Tools specific to that Editor's function.

11.3 Contextual Toolbar
A Toolbar or set of actions presented according to the current context.

It can depend on:

the selected object;

the active mode;

the module;

the Flow;

the procedure state.

This separation allows the interface to remain compact without removing advanced functionalities.

## 12. Toolbar and Layout
The Toolbar is an interface component and can be hosted in different regions of the Workspace, according to the Layout.

Its position does not change its function.

For example:

text
Workspace
│
├── Header
│
├── Toolbar
│
├── Area
│   └── Editor
│
└── Area
    └── Editor
A Toolbar can also be associated with a specific Editor:

text
Area
│
├── Toolbar
│
└── Editor
The Layout determines where the Toolbar is presented.

The functional context determines which actions it presents.

## 13. Toolbar and Commands
When a Toolbar action changes the persistent state of the application, its execution should normally occur through a Command.

For example:

text
Toolbar
   │
   ▼
Tool
   │
   ▼
Command
   │
   ▼
Application State
This allows operations executed by the Toolbar to participate in the mechanisms of:

undo;

redo;

operation history;

validation;

event logging.

The Toolbar must not directly manipulate the domain state to execute these operations.

## 14. Toolbar and Application State
The Toolbar must be reactive to the application state.

When the context changes, the relevant items must be updated.

Example:

text
Selection = None

[ Cut ]      disabled
[ Copy ]     disabled
[ Delete ]   disabled
After selecting a compatible object:

text
Selection = Mandible

[ Cut ]      enabled
[ Copy ]     enabled
[ Delete ]   enabled
The Toolbar presents the state received from the application; it must not duplicate or maintain a second source of truth for that state.

## 15. Toolbar Configuration
The composition of a Toolbar must be configurable.

A Toolbar can be built from a specification containing:

identification;

title;

position;

context;

action groups;

Tools;

separators;

menus;

availability conditions.

Conceptual example:

python
ToolbarSpec(
    id="modeling",
    title="Modeling",
    items=[
        "tool.select",
        "tool.move",
        "tool.rotate",
        Separator(),
        "tool.measure",
    ],
)
The specification describes how the Tools should be organized and presented, while the Toolbar implementation determines how that configuration will be materialized in the interface.

The specification must not duplicate the definition of the Tools. Tools are defined and registered independently of the Toolbar.

## 16. Design Principles
The implementation of CranioZ Toolbars must follow a set of principles:

16.1 Separation of Responsibilities
The Toolbar presents actions.

Tools execute operations.

Commands represent transactional state changes.

Services execute specialized operations.

The domain represents the fundamental concepts and rules of the application.

16.2 Contextuality
The Toolbar should present only the actions relevant to the current context whenever possible.

16.3 Consistency
The same Tool must behave consistently regardless of where it is presented.

16.4 Low Visual Intrusion
The Toolbar should provide quick access to operations without visually competing with the main content of the Editor.

16.5 Extensibility
Modules and plugins must be able to provide new Tools without directly modifying the Toolbar implementation.

16.6 Single State
The Toolbar must not maintain an independent copy of the application state.

16.7 Reusability
The same Tool must be able to be presented in different interface components.

16.8 Tool Independence
Tools must be defined independently of Toolbars.

An Editor selects the Tools it needs, and a Toolbar presents those Tools.

## 17. Conceptual Architecture
The relationship between the main elements can be represented as follows:

text
                         Tool Registry
                              │
                ┌─────────────┼─────────────┐
                │             │             │
             Tool A        Tool B        Tool C
                │             │             │
                └─────────────┼─────────────┘
                              │
                         Editor
                              │
                   declares required Tools
                              │
                              ▼
                          Toolbar
                              │
                         presents Tools
                              │
                              ▼
                            User
Modules and plugins can contribute new Tools:

text
Core ────────────┐
                 │
Module ──────────┼──► Tool Registry ───► Editor ───► Toolbar
                 │
Plugin ──────────┘
The Toolbar, therefore, constitutes a presentation layer for the available Tools, and not a mechanism for implementing those operations.

The architecture can be summarized as follows:

text
Tools      → what can be done
Editor     → which Tools are needed
Toolbar    → how the Tools are presented
User       → interacts with the Tools