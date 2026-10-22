# ADR-0007: Commands, Transactions, and Undo/Redo

**Status:** Accepted
**Date:** 2026-10-22
**Deciders:** Architecture team
**Related:** commands.md, scene.md, project.md §10, §13, §22, ADR-0002

---

## 1. Context

Every state-changing operation in CranioZ must pass through a single
mechanism that provides validation, transaction boundaries, undo/redo,
event publication, and auditability. Without such a mechanism, the
Scene would be mutated in at least four incompatible ways:

- Directly by Editors (ADR-0001 forbids this).
- Directly by Tools (tools.md forbids this).
- Directly by the Project Manager (project.md §10 forbids this).
- Directly by the AI assistant (overview.md §22 forbids this).

The `commands.md` document specifies the contract. This ADR records
the architectural decision and the consequences.

## 2. Decision

### 2.1 The Command mechanism is the only path to persistent mutation

A **Command** is an immutable data object that expresses an intent to
change persistent state. A **CommandHandler** validates, opens a
transaction, mutates the domain, commits, and publishes events. A
**CommandBus** routes Commands by type to their handlers.

    UI / AI / Script
    │
    ▼
    CommandDispatcher (from EditorContext or ToolContext)
    │
    ▼
    CommandBus (routes by type)
    │
    ▼
    CommandHandler
    ├── 1. Authorize
    ├── 2. Validate
    ├── 3. Open transaction
    ├── 4. Mutate domain / Scene
    ├── 5. Commit
    └── 6. Publish events


### 2.2 Commands are data, not behavior

A Command is a frozen dataclass. It does not have an `execute()`
method. The logic lives in the Handler. This keeps Commands
serializable, testable without a runtime, and usable by any caller
(UI, AI, MCP, script).

### 2.3 The transaction boundary is per Command

Each Command maps to exactly one transaction. If a Command mutates
multiple domain objects, all mutations happen within a single logical
transaction. If any step fails, the transaction is rolled back, the
domain state is restored, and no events are published.

### 2.4 Events are published only after commit

A CommandHandler must never publish an event before the transaction
commits. This guarantees that the UI never reacts to a state that
was rolled back.

### 2.5 Undo/Redo is command-based

CranioZ uses a Command History, not state snapshots. Each reversible
Command stores a compensating Command. The UI triggers `undo()` via
the CommandStack, which dispatches the compensating Command. A
Command declares `is_reversible`; irreversible Commands require
explicit confirmation.

### 2.6 No UI dependencies

Commands, Handlers, and the CommandBus must have zero dependencies on
PySide6, Qt, or VTK. They belong to the Application layer. The UI
receives a CommandDispatcher through its context (ADR-0002) and
dispatches Commands; it does not know the Handler.

## 3. Rationale

### 3.1 Single gatekeeper

`project.md` §10 requires "explicit transaction boundaries for
multi-step state-changing operations". `commands.md` §1 lists
validation, transaction boundaries, undo/redo, auditability, and
decoupling as the five reasons. A single entry point makes all five
possible.

### 3.2 Compatibility with ADR-0002

ADR-0002 established the hybrid `EditorContext`. `CommandDispatcher`
is a shared reference across all Editors — it is global, immutable to
the Editor, and cheap to share. The classification rule in ADR-0002
§3.2 places it unambiguously in the shared field group.

### 3.3 Compatibility with AI/MCP

`overview.md` §22 requires that AI executes commands through the same
mechanism as human-triggered Tools. A Command that does not depend on
the UI can be dispatched by an MCP adapter identically to how it is
dispatched by a Tool. This is not possible if Commands contain
behavior.

### 3.4 Auditability

Each Command carries `command_id` and `metadata` (actor, project_id,
timestamp). The CommandStack records every dispatched Command,
producing an audit trail that maps directly to `project.md` §28
(security, privacy, auditability).

## 4. Consequences

### 4.1 Positive

- One path for every state mutation.
- Undo/redo, auditing, and AI integration become possible without
  changing the domain.
- Commands are serializable and testable without Qt.
- The Scene is protected from direct mutation by Editors.

### 4.2 Negative

- Boilerplate: every operation requires a Command class and a Handler.
  The commands.md §10 roadmap acknowledges this and lists the
  implementation order.
- The CommandDispatcher becomes a required dependency of every Editor
  and Tool. This is a cost the architecture explicitly accepts.

### 4.3 Neutral

- Commands are not Events. An Event is a fact; a Command is an intent.
  The distinction is fundamental and documented in commands.md §2.1.

## 5. Rules applied by this ADR

1. Every persistent state mutation passes through a Command.
2. Commands are frozen data; no `execute()` method.
3. Each Command maps to one transaction.
4. Events are published only after commit.
5. Undo/Redo uses compensating Commands, not state snapshots.
6. Commands, Handlers, and the CommandBus have no Qt dependency.
7. The UI dispatches Commands through a CommandDispatcher.
8. AI and MCP dispatch Commands through the same CommandDispatcher.
9. Every Command carries `command_id` and metadata.
10. Irreversible Commands require explicit confirmation.

## 6. Rejected alternatives

### 6.1 Direct mutation by Editors

Rejected. Violates ADR-0001, ADR-0002, and `overview.md` §3.6.

### 6.2 Direct mutation by the Project Manager

Rejected. Violates `project.md` §10. The Manager coordinates the
lifecycle; individual mutations belong to Commands.

### 6.3 State snapshots for Undo/Redo

Rejected. Snapshots of the Scene are expensive (large geometry
payloads), lossy (they cannot capture intent), and incompatible with
the audit trail. Command-based undo is the standard solution and is
what `commands.md` §5.2 specifies.

### 6.4 Commands with `execute()` methods

Rejected. Couples Commands to the domain and makes them
non-serializable. Commands are data.

### 6.5 A separate "Operations" layer

Rejected. Adds a layer without adding value. Commands are the
operations.

## 7. Implementation order

Per `commands.md` §10:

1. `application/commands/base.py` — Command, CommandHandler,
   CommandBus Protocols.
2. `application/commands/bus.py` — CommandBus implementation.
3. `application/commands/stack.py` — CommandStack for Undo/Redo.
4. `application/events/bus.py` — connect CommandHandler to EventBus
   (already exists as `application/event_bus.py`).
5. `domain/errors.py` — ApplicationError and DomainError base classes.
6. `ui/editors/editor_context.py` — inject CommandDispatcher
   (already exists; needs the field).

## 8. Summary

The Command mechanism is the single gatekeeper for persistent state
mutation in CranioZ. It is data-only, transaction-bounded, and
UI-independent. It is the prerequisite for Scene, WorkflowEngine,
and AI integration. Without it, the architectural invariants in
`overview.md` §25 (explicit transaction boundaries, single entry
point for state changes) cannot be enforced.