# AGENTS.md
# CranioZ — Guidelines for AI Agent Development

## 1. Purpose

This document defines the operational guidelines for AI agents contributing to the CranioZ project.

All agents must follow these instructions when analyzing, creating, modifying, or debugging the project's code and documentation.

The primary objectives are:
- To maintain architectural consistency.
- To minimize unnecessary code changes.
- To optimize token consumption without compromising implementation quality.
- To keep development tasks focused and subject to independent verification.
- To preserve developer control over architectural decisions.
- To treat testing as an integral part of development; whenever appropriate, after creating files or functions, the corresponding tests must be created to validate system robustness.
- To define a restricted scope of actions, test them, and bring them to completion.

These guidelines apply regardless of the AI ​​model or development tool being used.

## 2. General Development Principles

1. Be concise and objective in all development activities.
2. Prioritize minimal, targeted changes over sweeping refactors.
3. Preserve the existing architecture, naming conventions, and established patterns.
4. Do not introduce unnecessary abstractions, dependencies, files, or complexities.
5. Reuse existing implementations and components whenever appropriate.
6. Do not modify code unrelated to the task at hand.
7. Do not assume that a technically feasible change is architecturally desirable.
8. If requirements are unclear, request clarification before proceeding based on significant assumptions. Whenever possible, consolidate all relevant questions into a single message. **The agent must resolve the requested issue by making the smallest appropriate change.**

## 3. Documentation-Driven Workflow

The documentation located in the `..` directory serves as the primary reference for development.

Before implementing or modifying code, the agent must:

1. Identify the relevant documentation.
2. Read only the documents necessary for the task at hand.
3. Understand the intended architecture, responsibilities, and implementation status.
4. Verify that the proposed changes align with previously established decisions.

Documentation should guide the implementation; it must not be rewritten simply to justify an implementation that contradicts previously established decisions.

### 3.1 User Interface (UI) Implementation

When implementing or modifying user interface elements:

- Existing UI prototypes and design documentation serve as the primary visual references.
- Follow the documented layout, hierarchy, spacing, visual conventions, and interaction patterns.
- Reuse existing widgets and components whenever possible.
- Consult the widget catalog before creating new UI components.
- Do not redesign elements or introduce new visual patterns on your own without approval from a developer.

If a prototype does not cover an important interaction or visual detail, discuss the proposed solution before making significant design decisions.

### 3.2 Incomplete or Conflicting Documentation

If the documentation is incomplete, contradictory, or insufficient:

1. Identify the specific issue.
2. Explain its impact on the implementation.
3. Present a concise proposal.
4. Await approval from a developer when an architectural or structural decision is required.

Do not establish new architectural conventions on your own. ## 4. Architectural Decisions

Architectural decisions are the responsibility of the developer.

Agents must not, on their own initiative:

- Alter established architectural boundaries.
- Introduce new architectural or infrastructure patterns.
- Change the responsibilities of application modules or layers.
- Modify public APIs or domain contracts without approval.
- Introduce new dependencies without approval.
- Perform extensive refactoring within the scope of an unrelated task.

For decisions that may affect the architecture:

1. Explain the current situation.
2. Identify the problem or limitation.
3. Present the proposed solution and its implications.
4. Wait for explicit approval from a developer.

Agents may independently make minor implementation decisions that remain within established architectural boundaries.

## 5. Code Development Guidelines

### 5.1 Token Efficiency and Context Management

The development environment may operate using models with limited context windows and varying token costs. Agents must optimize context consumption and execution efficiency.

Follow these practices:

- Keep responses concise.