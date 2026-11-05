1. pyproject.toml + empty folder structure
2. core/results/models.py        (dataclasses, no dependencies)
3. tests/test_results.py         (round-trip serialization)
4. core/execution/engine.py      (subprocess + threads + cancellation)
5. tests/test_engine.py          (using a fake subprocess)
6. core/persistence/store.py     (SQLite)
7. tests/test_persistence.py
8. adapters/ruff/adapter.py
9. tests/test_ruff_adapter.py    (using a fake or real Ruff)
10. ui/main_window.py            (minimal PySide6)
11. main.py / entry point


Phase 0 — Foundation and Contract
- Define the `ExecutionResult` model (a typed dataclass, independent of the UI).
- Define the persistence model (SQLite for executions + an artifacts directory).
- Define environment resolution (project root, `.venv`, configuration precedence).
- Definition of done: A mock `ExecutionResult` is serialized/deserialized and retrieved from the history in a unit test.

Phase 1 — Execution Engine + 1 Reference Adapter
- Implement the Engine (handling subprocesses, `stdout`/`stderr`, cancellation, and exit codes).
- Implement the Ruff adapter (the simplest and fastest option).
- Implement a minimal UI: a window with a "Run Ruff" button, a log, and a history view.
- Definition of done: Running Ruff via the UI yields a structured result; the process can be cancelled mid-execution, and the history persists across sessions.

Phase 2 — Verification and Comprehensive Testing
- Adapters: Mypy, Pytest, Coverage.
- Consolidated results + failure visualization.
- Definition of done: Each adapter includes a test using a mock subprocess; Pytest failures display a parsed traceback rather than just raw text.

Phase 3 — Dashboard
- Aggregates results from previous phases (does not trigger any executions).
- Displays status by area (verification, testing, coverage) along with recent history.
- Definition of done: The dashboard reflects actual past executions without initiating any new tasks.

Phase 4 — Code Extraction (reusing an existing utility)
- Integrate the existing utility + TXT-based profiles.
- Definition of done: Profiles can be saved and reused; the extraction process does not modify the source files.

Phase 5 — Documentation
- Sphinx and/or MkDocs, depending on the repository's actual structure.
- Link validation + display of warnings.
- Definition of done: Documentation builds can be triggered via the UI, and errors are navigable. Phase 6 — Build (executable only)
- PyInstaller + build profiles.
- Level 1 validation (existence/integrity of artifacts).
- Definition of done: generated executable opens on a clean machine (manual smoke test passed).

Phase 7 — Installer
- Inno Setup or NSIS.
- Level 2 validation (installation/uninstallation in a controlled environment).
- Definition of done: installer is generated, installation succeeds, the app opens, and uninstallation leaves no residual files.

Phase 8 — Architecture & Reports
- Import Linter (enforced rule) first.
- Dependency visualization second (optional, high cost).
- Consolidated reports last (dependent on all previous steps).
- Definition of done: Import Linter causes the build to fail when a contract is violated; 
reports reference execution and artifacts by ID.

Phase 9 — Dogfooding and hardening
- Use the DC (Development Controller/Tool) for 2–4 weeks within the actual development workflow.
- Resolve friction points; add structured logging to the DC itself.
- Definition of done: no development task requires manual terminal intervention for processes covered by the DC.



