# AGENTS.md
# CranioZ — AI Agent Development Guidelines

## 1. Purpose

This document defines the operational guidelines for AI agents contributing to the CranioZ project.

All agents must follow these instructions when analyzing, creating, modifying, or debugging project code and documentation.

The primary objectives are:
- Maintain architectural consistency.
- Minimize unnecessary code changes.
- Optimize token consumption without compromising implementation quality.
- Keep development tasks focused and independently verifiable.
- Preserve developer control over architectural decisions.
- Create a small scope of actions, test them, and finalize them.

These guidelines apply regardless of the AI model or development tool being used.

## 2. General Development Principles

1. Be concise and objective in all development activities.
2. Prefer minimal, targeted changes over broad refactoring.
3. Preserve existing architecture, naming conventions, and established patterns.
4. Do not introduce unnecessary abstractions, dependencies, files, or complexity.
5. Reuse existing implementations and components whenever appropriate.
6. Do not modify unrelated code.
7. Do not assume that a technically possible change is architecturally desirable.
8. When requirements are unclear, ask for clarification before proceeding with significant assumptions. Group all relevant questions into a single message whenever possible.

**The agent must solve the requested problem with the smallest appropriate change.**

## 3. Documentation-First Workflow

The documentation located in the `..` directory is the primary reference for development.

Before implementing or modifying code, the agent must:

1. Identify the relevant documentation.
2. Read only the documents necessary for the current task.
3. Understand the intended architecture, responsibilities, and implementation status.
4. Verify that the proposed changes are consistent with existing decisions.

Documentation must guide implementation, not be rewritten to justify an implementation that contradicts established decisions.

### 3.1 UI Implementation

When implementing or modifying user interface elements:

- Existing UI prototypes and design documentation are the primary visual references.
- Follow the documented layout, hierarchy, spacing, visual conventions, and interaction patterns.
- Reuse existing widgets and components whenever possible.
- Consult the widget catalog before creating new UI components.
- Do not independently redesign or introduce new visual patterns without developer approval.

If the prototype does not cover an important interaction or visual detail, discuss the proposed solution before making significant design decisions.

### 3.2 Conflicting or Missing Documentation

If documentation is incomplete, contradictory, or insufficient:

1. Identify the specific issue.
2. Explain its impact on the implementation.
3. Present a concise proposal.
4. Wait for developer approval when an architectural or structural decision is required.

Do not silently establish new architectural conventions.

## 4. Architectural Decisions

Architectural decisions belong to the developer.

Agents must not independently:

- Change established architectural boundaries.
- Introduce new architectural patterns or infrastructure.
- Change module responsibilities or application layers.
- Modify public APIs or domain contracts without approval.
- Introduce new dependencies without approval.
- Perform broad refactoring under the scope of an unrelated task.

For decisions that may affect the architecture:

1. Explain the current situation.
2. Identify the problem or limitation.
3. Present the proposed solution and its implications.
4. Wait for explicit developer approval.

Agents may independently make small implementation decisions that remain within established architectural boundaries.

## 5. Code Development Guidelines

### 5.1 Token Efficiency and Context Management

The development environment may operate with models that have limited context windows and different token costs. Agents must optimize context consumption and execution efficiency.

Follow these practices:

- Keep responses short and technically precise.
- Avoid unnecessary explanations and repetitive summaries.
- Read only files relevant to the current task.
- Avoid loading entire directories or large files when targeted inspection is sufficient.
- Prefer focused diffs over rewriting complete files.
- Avoid repeating information already established in the conversation or documentation.
- Avoid unnecessary tool calls and repeated code inspections.
- Do not generate extensive plans for straightforward tasks.
- Report only relevant implementation details and remaining issues.

For planning purposes, a straightforward task generally:
- Modifies up to 2–3 files.
- Does not change public interfaces or architectural contracts.
- Does not introduce new dependencies or architectural decisions.
- Has clearly defined requirements and expected results.

Tasks exceeding these criteria may require a brief implementation plan before execution.

Token efficiency must never compromise correctness, maintainability, or architectural consistency.

### 5.2 Implementation

- Follow the existing Python-first development approach.
- Use established project conventions and type annotations.
- Prefer clear, maintainable, and explicit implementations.
- Avoid premature optimization.
- Avoid unnecessary compatibility layers and speculative abstractions.
- Keep responsibilities separated according to the existing architecture.
- Preserve existing behavior unless the task explicitly requires changing it.

Do not implement additional features beyond the requested scope.

### 5.3 Scope Control

Before modifying code, establish the exact scope of the task.

During implementation:

- Modify only the necessary files.
- Avoid opportunistic cleanup.
- Do not rename unrelated classes, functions, or variables.
- Do not reorganize directories without approval.
- Do not introduce temporary production code for debugging.

If the task reveals a separate problem, report it instead of expanding the current implementation.

## 6. Testing and Debugging

### 6.1 Testing Policy

- All functional tests are performed manually by the developer.
- Do not create automated tests or test suites unless explicitly requested.
- Do not assume responsibility for final functional validation.
- The developer is responsible for validating the implemented functionality.

Agents may perform basic code inspection and focused technical checks when necessary. These checks do not replace manual testing.

### 6.2 UI Debugging Scripts

Whenever code creates or modifies UI components, the agent must:

1. Create a visual debugging script inside the `scripts` directory.
2. Organize the script according to the existing directory structure.
3. Ensure the script allows the developer to independently launch and inspect the modified UI component whenever practical.
4. Reuse the application's existing initialization, theme, and widget infrastructure whenever appropriate.

**Creating the visual debugging script is mandatory. Executing it and visually validating the result are the developer's responsibility.**

UI modifications are not considered visually validated until explicitly approved by the developer.

### 6.3 Git and Commits

- All Git commits are performed manually by the developer.
- Never create commits automatically.
- Never stage changes automatically.
- Never amend, reset, or rewrite Git history.
- Do not perform Git operations that alter repository history.

The agent must leave all modifications available for developer inspection and manual commit.

## 7. Documentation Maintenance

Documentation must remain synchronized with the implementation.

### 7.1 implementation_plan.md

Update the implementation plan when a task:
- Completes or changes an implementation stage.
- Changes the scope or technical approach.
- Changes the status of planned features or deliverables.
- Introduces relevant dependencies or blockers.

Do not update the document for isolated code corrections that do not affect implementation status or scope.

### 7.2 next_steps.md

Update the next steps document when a task:
- Completes previously planned activities.
- Changes the sequence of implementation.
- Introduces new tasks, dependencies, or blockers.
- Changes the recommended immediate development priorities.

Keep the sequence practical, concise, and consistent with the implementation plan.

### 7.3 Documentation Consistency

When implementation changes affect other technical documentation, update the corresponding documents as well.

Do not create redundant documentation or duplicate architectural decisions across multiple files.

If documentation changes require an architectural decision, obtain developer approval first.

## 8. Task Completion and Development Workflow

### 8.1 Completion Protocol

A development task is considered implemented when:

1. The requested code changes are complete.
2. The implementation follows existing documentation and architecture.
3. Relevant code inspection and technical checks have been performed.
4. UI debugging scripts have been provided when applicable.
5. `implementation_plan.md` and `docs/development/planning/next_steps.md` have been updated when the task changes implementation status, scope, or priorities.
6. Pending manual validation is clearly identified.

The developer retains responsibility for manual validation, visual approval, and Git commits.

### 8.2 Step Completion Notification

Development activities should be divided into small, well-defined implementation steps.

Whenever an implementation step is completed, the agent must:

1. Explicitly notify the developer that the step is complete.
2. Briefly summarize the result.
3. Identify any pending manual validation.
4. Indicate whether the next step can proceed independently.

When a step or independent task is completed, recommend starting a new conversation in the IDE chat before beginning the next independent task.

The purpose is to keep the active context small, reduce accumulated conversation history, and improve implementation efficiency.

Do not continue into a new independent implementation task without making the previous step's completion clear.

### 8.3 Final Response

At the end of each task, provide a concise report containing:

- **Implemented:** What was changed.
- **Files:** Relevant modified or created files.
- **Validation:** What was checked and what remains for manual validation.
- **Documentation:** Which planning documents were updated.
- **Pending:** Unresolved issues or decisions requiring developer input.
- **Next Step:** Recommended next action and whether a new IDE conversation is recommended.

Avoid lengthy implementation narratives.

## 9. Developer Authority

The developer has final authority over:

- Architecture and design decisions.
- UI design and visual approval.
- Implementation priorities.
- Acceptance of proposed solutions.
- Final code validation.
- Git commits and repository history.

Agents are responsible for implementing approved requirements accurately and efficiently.

**When in doubt, preserve the existing architecture and ask before making significant changes.**

---

**Core principle: Follow the documentation, respect the architecture, minimize changes, conserve tokens, manage context, and keep the developer in control.**