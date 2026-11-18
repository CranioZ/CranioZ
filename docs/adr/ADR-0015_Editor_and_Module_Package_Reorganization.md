# ADR-0015: Editor and Module Package Reorganization

**Status:** Accepted
**Date:** 2026-11-17
**Deciders:** CranioZ Architecture Team
**Related:** ADR-0013, ADR-0014

## Context

The CranioZ codebase originally placed Editor implementations under `ui/editors/`, coupling functional Editors to the Workspace presentation layer. This structure made it difficult to implement new Editors (such as the Professional module planned for Sprint L) without creating circular dependencies between the Workspace and the Editors.

Additionally, the Module system's contracts and built-in implementations were mixed together under `modules/`, making discovery and boundary enforcement harder.

## Decision

We reorganize the packages as follows:

1. **`cranioz/editors/`** becomes the canonical package for all Editor-related code, independent of `ui/`.
   - `editors/core/editor/`: Editor contracts (base, context, registry, placeholder).
   - `editors/core/view/`: View contracts (view, layout renderer, layout spec).
   - `editors/views/`: Reusable visualization implementations (MPR, 3D viewport).
   - `editors/view_overlays/`: Reusable View-level overlays (gizmos, rulers).
   - `editors/builtin/`: Concrete functional Editors (Tomography, MeshDebug).

2. **`cranioz/modules/core/`** contains Module contracts and infrastructure (loader, registry, errors).
   **`cranioz/modules/builtin/`** contains concrete Module implementations.

3. **`cranioz/ui/workspace/`** retains all Workspace composition responsibilities (Areas, EditorStack, layout rendering).

4. **Dependency rules** are enforced via AST-based architecture tests:
   - `modules.core` must not import `editors`.
   - `editors.core.*` must not depend on concrete Editors or Modules.
   - `editors.core.*` may import `ThemeService` but not `ThemeCompiler`.
   - `ui.workspace` must not import concrete Editor implementations.
   - `cranioz.__main__` and `ui.main_window` are the approved composition root.

## Consequences

- **Positive:** Editors can be implemented independently of the Workspace. Modules remain declarative and do not depend on concrete Editors. The architecture is prepared for Sprint L (Professional module).
- **Negative:** The refactoring touches many files and imports. The `ui/editors/` package is removed.
- **Neutral:** The `ThemeService`, `IconProvider`, `Toolbar`, `ToolRegistry`, and `ToolContext` remain in `ui/` as approved presentation dependencies. Their migration to a `presentation/` package is deferred to a future ADR.

## Compliance

- `tests/architecture/test_dependency_boundaries.py` enforces the dependency rules.
- All tests pass after the refactoring.
- `ruff check`, `ruff format --check`, and `mypy src` are clean.