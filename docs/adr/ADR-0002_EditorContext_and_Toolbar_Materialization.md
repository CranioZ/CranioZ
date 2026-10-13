Status: Accepted
Date: 2026-10-13
Deciders: Architecture team
Related: ADR-0001_Area_and_Editor.md, editors.md, workspace_en.md,
         workspace-implementation.md, tools.md, toolbar.md

---

# 1. Context

Two decisions shape how the Workspace materializes a `ModuleUISpec`:

1. How many `EditorContext` instances exist, and what is shared between
   them.
2. Who creates the `Toolbar` widgets — the `LayoutBuilder` or the
   `LayoutRenderer`.

These decisions are interdependent. Both determine what "materialize"
means in the Workspace, and both affect whether the `LayoutBuilder`
remains a pure, Qt-free composition step. They are recorded together
for that reason.

---

## 1.1 EditorContext

The `EditorContext` is the controlled set of dependencies an Editor
receives at insertion time. The architecture document (`editors.md`
§15) already defines its intended shape:

    EditorContext
    ├── SceneQuery
    ├── SelectionService
    ├── CommandDispatcher
    ├── EventSubscription
    ├── ViewStateStore
    └── EditorServices

Two incompatible readings existed:

**Reading A — Shared context.**
A single `EditorContext` instance is created and passed to every
Editor in the composition.

**Reading B — One context per Editor.**
Each Editor receives its own `EditorContext` instance, with its own
`editor_id` and its own `ViewStateStore`.

Reading A is simpler to implement but breaks well-documented
invariants:

- `ViewStateStore` is explicitly per-Editor in `editors.md` §16.
- ADR-0001 states that two `Viewport3DEditor` instances are two
  independent instances.
- `EditorContext.editor_id` would have no consistent value if the same
  instance were shared among multiple Editors.

Reading B preserves those invariants, but raises a new question: if
`SceneQuery`, `CommandDispatcher` and `EventSubscription` are the same
for every Editor, creating a fresh copy per Editor would duplicate
expensive, global resources.

Neither reading alone is correct.

## 1.2 Toolbar materialization

A `Toolbar` is a Qt widget internal to an Editor (ADR-0002 is the
present document; see also `toolbar.md` and `tools.md`). It is
declared by a `ToolbarSpec` and materialized with the help of a
`ToolRegistry` and a `ThemeService`.

Two incompatible readings existed:

**Reading A — LayoutBuilder creates the Toolbar widget.**
The `LayoutBuilder` resolves `editor.toolbar_specs()` and creates
the Qt widget. The `LayoutRenderer` only places it.

**Reading B — LayoutRenderer creates the Toolbar widget.**
The `LayoutBuilder` produces pure data. The `LayoutRenderer`
materializes both the Editor's `content_widget()` and the
`Toolbar` widgets declared by `editor.toolbar_specs()`.

Reading A contradicts the contract of the `LayoutBuilder`, which is
defined as a pure composition step (`workspace-implementation.md`,
Phase 5):

> LayoutBuilder consumes a ModuleUISpec and produces a LayoutTree.

It also forces the `LayoutBuilder` to depend on Qt, requires a
`QApplication` for its tests, and duplicates the `LayoutRenderer`'s
responsibility of materializing widgets.

Reading B keeps the `LayoutBuilder` pure and gives the
`LayoutRenderer` sole responsibility for widget materialization. The
cost is that the `LayoutRenderer` must receive a `ToolRegistry` and a
`ThemeService` — which it needs anyway to materialize Toolbars.

---

# 2. Decision

## 2.1 EditorContext — hybrid model

A single `EditorContext` instance is created **per Editor**.

Within each instance:

- Fields whose values are **specific** to the Editor (identity,
  presentation state, per-Editor configuration) are isolated. Each
  Editor receives its own value or its own new instance.

- Fields whose values are **shared** between Editors (read-only
  queries, global dispatchers, event buses) hold a **reference to the
  same object**. They are not duplicated.

Conceptually:

    EditorContext (one per Editor)
    ├── editor_id            ── specific
    ├── extras               ── specific (copy)
    ├── view_state           ── specific (new instance)
    │
    ├── scene_query          ── shared (reference)
    ├── command_dispatcher   ── shared (reference)
    ├── event_subscription   ── shared (reference)
    └── editor_services      ── shared (reference)

This is a shallow copy with per-Editor overrides: the container is new
per Editor; the shared references are not copied.

## 2.2 Toolbar materialization — LayoutRenderer

The `LayoutBuilder` does **not** create Qt widgets. It produces pure
domain structures: `Area`, `Editor`, `LayoutTree`, `AreaManager`, and
`BuildResult`.

The `LayoutRenderer` materializes **all** widgets:

- One `Area` widget per `Area`.
- One `QSplitter` per `Split`.
- One Editor widget per `Editor`, obtained via
  `editor.content_widget()`.
- One `Toolbar` widget per `ToolbarSpec` returned by
  `editor.toolbar_specs()`.

The `LayoutBuilder` never imports `PySide6` and never requires a
`QApplication`.

## 2.3 Extension point

The `LayoutBuilder.build()` method accepts an optional
`shared_context: dict[str, Any]` parameter. Its values are propagated
by reference into every `EditorContext` created during that build.

The `LayoutBuilder` does not interpret the contents of
`shared_context`. Deciding what belongs there is the responsibility of
the caller (typically the `Workspace`).

This provides a stable extension point for future shared services
(`SceneQuery`, `CommandDispatcher`, `EventSubscription`) without
changing the `LayoutBuilder` contract when those services are
implemented.

---

# 3. Rationale

## 3.1 The hybrid model preserves invariants without duplicating resources

Reading A (shared context) breaks three documented invariants:

- `ViewStateStore` per Editor (`editors.md` §16).
- Two `Viewport3DEditor` instances are independent (ADR-0001).
- `EditorContext.editor_id` has a single, unambiguous value.

Reading B (one context per Editor, fully isolated) preserves those
invariants but duplicates global resources (`SceneQuery`, dispatchers,
event subscriptions). Those resources are the same for every Editor,
are often expensive to build, and are read-only for the Editor.

The hybrid model preserves the invariants of Reading B while
sharing the resources of Reading A. It is not a compromise: it is the
correct application of two distinct rules to two distinct kinds of
field.

## 3.2 The classification rule is explicit

The rule that distinguishes shared fields from specific fields is
stated once, in this ADR, and can be applied to every future field of
`EditorContext`:

A field is **shared** when **all** of the following are true:

1. Its value is immutable to the Editor, or mutations are
   thread-safe by design.
2. Its value is global to the project or session, not to the Editor.
3. Building it is expensive.
4. Two Editors seeing the same value is correct, not a bug.

A field is **specific** when **any** of the following is true:

1. It holds mutable state that must not leak between Editors.
2. It is identified by `editor_id`.
3. It is cheap to build.
4. Two Editors sharing it would be a bug.

This rule eliminates case-by-case debate. New fields are classified by
inspecting their nature, not by preference.

## 3.3 The LayoutBuilder must remain pure

The `LayoutBuilder` is defined as a pure composition step. Making it
create Qt widgets would:

- Force a `QApplication` for its tests, slowing them and making them
  brittle.
- Duplicate the `LayoutRenderer`'s responsibility.
- Split the widget lifecycle across two classes, with no single owner
  of creation and disposal.
- Violate the layering rule that separates composition logic from
  presentation.
- Serialize development: today, the `LayoutBuilder` is testable
  before the `LayoutRenderer` exists.

Keeping the `LayoutBuilder` Qt-free preserves all of these properties
at the cost of adding a `ToolRegistry` and a `ThemeService` to the
`LayoutRenderer` constructor — which it needs anyway.

## 3.4 Toolbars belong to the Editor

ADR-0002 (this document) and ADR-0001 establish that a Toolbar is
internal to an Editor, not to an Area and not to the Workspace. The
Editor declares its Toolbars via `toolbar_specs()`. The
materialization is performed by the component that materializes the
Editor — the `LayoutRenderer`. Ownership and materialization are
therefore consistent: the Editor declares, the `LayoutRenderer`
materializes.

The Workspace never hosts a Toolbar widget. The Area never hosts a
Toolbar widget.

## 3.5 Hybrid and pure-builder combine cleanly

The hybrid `EditorContext` and the pure `LayoutBuilder` reinforce each
other:

- The builder creates one context per Editor, isolating specifics.
- The builder propagates shared resources by reference via
  `shared_context`, without interpreting them.
- The builder never touches Qt, so it never needs to know how Toolbars
  are materialized.
- The renderer materializes widgets and consumes the same
  `EditorContext` instances the builder produced.

Neither decision depends on the other, but together they form the
complete answer to "how does a `ModuleUISpec` become a live UI?".

---

# 4. Consequences

## 4.1 Positive consequences

- **Documented invariants are preserved.** `ViewStateStore` is per
  Editor. Two Editors with the same `editor_id` are independent.
  `editor_id` on the context always refers to its own Editor.

- **Global resources are not duplicated.** `SceneQuery`,
  `CommandDispatcher` and `EventSubscription` are references, not
  copies. Cost is constant regardless of how many Editors exist.

- **`LayoutBuilder` remains pure.** No Qt import. No `QApplication`
  needed for its tests. They run in milliseconds.

- **`LayoutRenderer` owns widget lifecycle.** One place creates, one
  place disposes. The widget cache is rebuildable from the tree at any
  time.

- **Development can proceed in parallel.** The `LayoutBuilder` and
  its tests are complete before the `LayoutRenderer` exists.

- **Extension point is stable.** Adding `SceneQuery` later requires no
  interface change: it simply becomes a key in `shared_context`.

- **Classification rule is explicit and reusable.** Future fields of
  `EditorContext` are classified by a documented rule, not by
  preference.

## 4.2 Negative consequences

- **`LayoutRenderer` gains dependencies.** It must receive a
  `ToolRegistry` and a `ThemeService` in its constructor. This is
  expected: materializing a Toolbar requires resolving Tools and
  icons.

- **`EditorContext` is not a single object.** Callers must understand
  that the container is per Editor and that some fields are shared.
  The classification rule (§3.2) and the type structure make this
  explicit.

- **`shared_context` is untyped at the builder boundary.** The
  builder accepts `dict[str, Any]` and does not validate its contents.
  This is intentional (the builder must not know what services exist),
  but it means the caller is responsible for passing a coherent set.
  When the shared services are implemented, a stronger type
  (`SharedContext` dataclass) can replace the dict without changing
  the builder's behavior.

- **`extras` must be copied per Editor.** If passed by reference
  without copying, mutations in one Editor leak into others. The
  builder performs `dict(extras)` for each context. This is a
  documented responsibility of the builder, not an accident.

## 4.3 Neutral consequences

- **Field-by-field classification takes thought.** Every time a new
  field is added to `EditorContext`, the author must classify it
  according to §3.2. This is a small, deliberate cost — and it
  prevents the field from being added thoughtlessly.

---

# 5. Rules applied by this ADR

The following invariants are enforced by this decision:

1. Each Editor receives its own `EditorContext` instance.
2. `EditorContext.editor_id` always refers to its own Editor.
3. `EditorContext.extras` is copied per Editor; mutations do not leak.
4. `ViewStateStore` (and any future presentation state) is per Editor.
5. Shared services (`SceneQuery`, `CommandDispatcher`,
   `EventSubscription`) are propagated by reference, not copied.
6. The `LayoutBuilder` does not import Qt and does not require a
   `QApplication`.
7. The `LayoutBuilder` does not create widgets of any kind.
8. The `LayoutRenderer` is the sole materializer of widgets — Areas,
   Splits, Editors, and Toolbars.
9. A `Toolbar` widget is created by the `LayoutRenderer` from the
   `ToolbarSpec` returned by `editor.toolbar_specs()`.
10. The `LayoutBuilder.build()` accepts an optional `shared_context`
    mapping and propagates its values by reference into each
    `EditorContext`.
11. The `LayoutBuilder` does not interpret the contents of
    `shared_context`.
12. The classification rule in §3.2 governs every future addition to
    `EditorContext`.

---

# 6. Alternatives considered

## 6.1 A single shared EditorContext (Reading A for decision 1)

Rejected. Breaks `ViewStateStore`, breaks `editor_id` semantics,
breaks the independence of multiple Editors with the same
`editor_id`.

## 6.2 Fully isolated EditorContext (Reading B for decision 1)

Rejected. Duplicates global resources, which are expensive and
identical for every Editor. The hybrid model achieves the same
isolation for specifics without paying this cost.

## 6.3 LayoutBuilder creates Toolbar widgets (Reading A for decision 2)

Rejected. Breaks the purity of the `LayoutBuilder`. Forces a Qt
dependency into a class that is defined as Qt-free. Duplicates
materialization logic. Splits the widget lifecycle across two classes.

## 6.4 Editor materializes its own Toolbar widget

Considered and rejected as a general rule. Having each Editor create
its own `Toolbar` widget would push the `ToolRegistry` and
`ThemeService` dependencies into every Editor. The `LayoutRenderer`
already has these dependencies for its own purposes and is the
natural owner of widget creation. Editors declare; the renderer
materializes.

An Editor may still provide a convenience method that returns a fully
built widget, if a future Editor has unusual needs. This ADR does not
forbid it; it simply does not make it the default.

---

# 7. Example

## 7.1 The LayoutBuilder creates contexts (pure)

    shared = {
        "scene_query": request.scene_query,
        "command_dispatcher": request.command_dispatcher,
        "event_subscription": request.event_subscription,
    }

    for editor_id in editor_ids:
        editor = self._registry.create(
            editor_id,
            editor_id=editor_id,
            title=editor_id,
        )
        context = EditorContext(
            editor_id=editor_id,        # specific
            extras=dict(extras),        # specific (copy)
            view_state=ViewStateStore(),# specific (new)
            **shared,                   # shared (references)
        )
        editor.initialize(context)

No Qt import. No widget creation. The builder produces only domain
structures and their contexts.

## 7.2 The LayoutRenderer materializes widgets

    def _render_editor(self, editor: Editor) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        for toolbar_spec in editor.toolbar_specs():
            toolbar = Toolbar(
                spec=toolbar_spec,
                registry=self._tool_registry,
                theme=self._theme_service,
                context=editor.tool_context,
            )
            layout.addWidget(toolbar)

        layout.addWidget(editor.content_widget())
        return container

The renderer owns the Toolbar lifecycle. The builder never sees it.

---

# 8. Summary

Two decisions, one principle:

> **Per-Editor isolation for what is specific; shared references for
> what is common; and a single owner for widget materialization.**

The `EditorContext` is a per-Editor container whose specific fields
are isolated and whose shared fields reference global services.

The `LayoutBuilder` produces pure data and never touches Qt. The
`LayoutRenderer` materializes every widget — Areas, Splits, Editors,
and Toolbars.

The hybrid model is not a compromise between two positions. It is the
precise application of two distinct rules to two distinct kinds of
field. The pure builder is not an optimization. It is what keeps the
composition step testable, layer-correct, and developable in parallel
with the presentation step.