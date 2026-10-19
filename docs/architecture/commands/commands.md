# Commands

**Document type:** Architecture specification
**Status:** Living document
**Scope:** Definition, lifecycle, and execution of Application Commands in CranioZ.

---

## 1. Purpose

In CranioZ, every operation that changes the persistent state of the system must pass through a **Command**.

The Command mechanism is the single entry point for state mutation. It exists to provide:
- **Validation:** Ensuring a clinical operation is legal before it happens.
- **Transaction boundaries:** Guaranteeing atomicity (all-or-nothing).
- **Undo/Redo:** Providing a consistent history for the user.
- **Auditability:** Recording who did what, when, and with what parameters.
- **Decoupling:** Separating the user interface (UI) from the business rules (Domain).

This document defines the contracts, lifecycle, and responsibilities of Commands, CommandHandlers, and the CommandBus.

---

## 2. Core Concepts

The Command architecture is composed of four distinct elements:

| Component | Responsibility |
|---|---|
| **Command** | A declarative data structure representing an *intent* to change state. It contains the target and the parameters. |
| **CommandDispatcher** | The interface used by the UI (Editors, Tools, AI) to send a Command. |
| **CommandBus** | The routing mechanism that receives a Command and finds the appropriate Handler. |
| **CommandHandler** | The orchestrator that validates, executes, commits, and publishes events for a specific Command. |

### 2.1 Command is not an Event
- A **Command** expresses a *wish* or *intent*. It can be rejected. (e.g., `MoveMaxillaCommand`, `CreateProjectCommand`).
- An **Event** expresses a *fact* that has already happened. It cannot be rejected. (e.g., `MaxillaMovedEvent`, `ProjectCreatedEvent`).

Commands are handled *before* the transaction commits. Events are published *after* a successful commit.

### 2.2 Command is not a Tool
A **Tool** (`tools.md`) is the UI interaction (e.g., a button, a drag action). The Tool's responsibility is to gather parameters and create a Command. The Tool does not execute the Command itself.

---

## 3. The Command Lifecycle

The execution of a Command follows a strict, deterministic sequence:

```text
UI / AI / Script
       │
       ▼
CommandDispatcher (Context)
       │
       ▼
CommandBus (Routes by type)
       │
       ▼
CommandHandler
       │
       ├── 1. Authorize (Access Policy)
       ├── 2. Validate (Domain rules, geometry checks)
       ├── 3. Open Transaction
       ├── 4. Mutate Domain / Scene
       ├── 5. Commit Transaction
       └── 6. Publish Events (EventBus)

```

If any step between 2 and 5 fails, the transaction is rolled back, the domain state remains unchanged, and an Application Error is returned to the caller. No events are published on failure.

## 4. Contracts
### 4.1 The Command Contract
A Command is an immutable data structure. It carries identity (who/where), target (what), and parameters (how).

    from dataclasses import dataclass
    from typing import Any
    
    @dataclass(frozen=True)
    class Command:
        """Base contract for all Commands."""
        
        # Unique identifier of the command execution (for tracing)
        command_id: str
        
        # Optional: Contextual info (e.g., user_id, project_id)
        metadata: dict[str, Any]

*Example of a concrete Command:*

    @dataclass(frozen=True)
    class CreateProjectCommand(Command):
        patient_id: str
        project_name: str
        clinical_procedure: str


### 4.2 The CommandHandler Contract
Handlers are specific to a single Command type. They reside in the Application layer and coordinate the Domain and Infrastructure.

    from typing import Protocol, TypeVar, Generic
    
    TCommand = TypeVar("TCommand", bound=Command)
    TResult = TypeVar("TResult")
    
    class CommandHandler(Protocol, Generic[TCommand, TResult]):
        """Contract for executing a specific Command type."""
        
        def handle(self, command: TCommand) -> TResult:
            """
            Executes the command within a transaction boundary.
            Raises ApplicationError on validation failure.
            """
            ...


### 4.3 The CommandBus Contract
The CommandBus is the central router.

    class CommandBus(Protocol):
        def register(self, command_type: type[Command], handler: CommandHandler) -> None:
            """Registers a handler for a command type."""
            ...
    
        def dispatch(self, command: Command) -> Any:
            """
            Routes the command to its handler.
            Raises KeyError if no handler is registered.
            """
            ...

## 5. Transactions and Undo/Redo
### 5.1 Transaction Boundaries
A Command maps to exactly one transaction.

If a Command mutates multiple domain objects (e.g., moving the maxilla, updating the dental splint, and adjusting landmarks), all mutations happen within a single logical transaction.

The CommandHandler coordinates this. If an error occurs during any step, the TransactionManager rolls back the state to the beginning of the Command.

### 5.2 Undo/Redo
CranioZ uses a Command History to handle Undo/Redo, rather than state snapshots.

A Command declares whether it supports Undo/Redo:

    @dataclass(frozen=True)
    class MoveMaxillaCommand(Command):
        object_id: str
        translation_vector: tuple[float, float, float]
        
        # Default is True; Commands that trigger irreversible external operations 
        # (e.g., "Send Email", "Delete File from Disk") override this.
        is_reversible: bool = True


When a reversible Command is committed, the CommandStack stores the following:

The Command itself.

A compensating command (the UndoCommand).

A rollback snapshot (if necessary for complex geometric operations).

The UI (via EditorContext) triggers undo(). The CommandStack pops the last command and dispatches the inverse operation.

## 6. Events and the Command Mechanism
Events are the result of a Command, not a parallel mechanism.

Before Commit: The CommandHandler mutates the Domain and prepares an internal list of Events to publish.

After Commit: The CommandHandler sends the Events to the EventBus.

This ensures that the UI (or an external system) never reacts to an event that corresponds to a failed transaction.

Rule: A CommandHandler must never publish an event until the transaction has successfully committed.

## 7. Validation and Authorization
The Command mechanism is the gatekeeper. Validation happens in three layers:

1. Structural Validation (UI/Tool): The Tool checks if the UI parameters are well-formed (e.g., "Is the text field empty?"). This is a courtesy to the user.
2. Authorization (CommandHandler): The CommandHandler checks if the current user/session has the right to execute this command (e.g., ProjectAccessPolicy.can_update(project_id)).
3. Domain Validation (Domain Layer): The Domain objects validate the state transition (e.g., "Can a maxilla be moved if it is not segmented yet?"). If validation fails, a DomainError is raised, and the Handler rejects the Command.


    class MoveMaxillaHandler(CommandHandler):
        def handle(self, command: MoveMaxillaCommand):
            # 1. Authorization
            if not self.access_policy.can_update(command.metadata["project_id"]):
                raise PermissionDenied()
                
            # 2. Fetch
            maxilla = self.scene.query.get_maxilla(command.object_id)
            
            # 3. Domain Validation
            if not maxilla.is_valid_for_movement():
                raise DomainError("Maxilla must be segmented first.")
                
            # 4. Mutate & Transaction
            with self.transaction_manager.begin():
                maxilla.move(command.translation_vector)
                # Event will be published automatically on commit

## 8. Integration with the Rest of the System
### 8.1 In the UI (EditorContext and ToolContext)
Editors and Tools do not know about CommandHandlers. They receive a CommandDispatcher through their contexts (see ADR-0002).

    # Inside a Tool's execute() method
    def execute(self, context: ToolContext):
        command = MoveMaxillaCommand(...)
        context.command_dispatcher.dispatch(command)

### 8.2 With AI and MCP (Automation)
The AIAssistantEditor and MCP server (see overview.md §22) use the exact same CommandDispatcher and CommandBus as a human user.

* Human UI: Tool -> CommandDispatcher.dispatch() -> CommandBus
* AI UI: Prompt -> CommandDispatcher.dispatch() -> CommandBus

This is the fundamental guarantee of auditability and security: AI cannot bypass validation or authorization because it uses the same entry point.

### 8.3 With the Workspace and Scene
* The Workspace and Areas do not interact with Commands directly.
* The Scene contains the state. It is mutated by the Domain layer, which is called by the CommandHandler. The Scene then emits its own Domain Events (e.g., ObjectTransformed), which the UI listens to.

Design Principles
1. One Command, One Handler: A Command type maps to exactly one Handler. If you need to do two things, use one Handler that orchestrates both operations within a single transaction.
2. Commands are Data: Commands must not contain logic (no execute() method inside the Command). The logic lives in the Handler.
3. Immutability: Commands are frozen. They represent a point-in-time intent and should not be mutated after creation.
4. No UI Dependencies: Commands, Handlers, and the Bus must have zero dependencies on PySide6, Qt, or VTK. They belong to the Application layer.
5. Errors are Information: A failed Command must return a structured Application Error (e.g., ProjectNotFound, InvalidGeometry) that the UI can display clearly, rather than a generic exception.
6. Explicit Reversibility: Every Command must declare whether it is reversible. For irreversible Commands (e.g., ExportPdfCommand), the UI must request explicit confirmation.

## 10. Implementation Roadmap
To implement the Command mechanism in the CranioZ codebase:

1. application/commands/base.py: Create the Command, CommandHandler, and CommandBus interfaces.
2. application/commands/bus.py: Implement the CommandBus router.
3. application/commands/stack.py: Implement the CommandStack for Undo/Redo.
4. application/events/bus.py: Connect the CommandHandler to the EventBus (publish on commit).
5. domain/errors.py: Define the base ApplicationError and DomainError.
6. ui/editors/editor_context.py: Inject the CommandDispatcher into the EditorContext (ADR-0002).