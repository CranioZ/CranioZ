# Testing in CranioZ

## 1. Purpose

This document describes how CranioZ is tested: the tools, the structure, the levels, the conventions, and the boundaries of what is and is not covered.

It is intended for contributors who need to understand, extend, or review the test suite. It is not a tutorial on writing tests in general; it documents the specific decisions of this project.

---

## 2. Tools

| Tool | Role |
|---|---|
| **pytest** | Test runner and assertion framework |
| **pytest-qt** | Qt widget testing, `QApplication` lifecycle, signal waiting |
| **pytest-cov** | Coverage measurement |
| **pytest-benchmark** | Performance benchmarks (opt-in, not part of the default suite) |
| **ruff** | Formatting, imports, style, and common lint errors |
| **mypy** | Static type checking |

The three checks run in CI on every push:

```bash
ruff format --check .
ruff check .
mypy src
pytest -q
```

A piece is green only when all four pass.

## 3. Structure
The test tree mirrors the source tree:

    src/cranioz/                      tests/
    ├── domain/                       ├── unit/
    │   ├── project/                  │   ├── domain/
    │   │   ├── project.py            │   │   ├── project/
    │   │   └── project_id.py         │   │   │   ├── test_project.py
    │   └── patient/                  │   │   │   └── test_project_id.py
    │       ├── enums/                │   │   └── patient/
    │       ├── sections/             │   │       ├── enums/
    │       └── patient.py            │   │       ├── sections/
    ├── application/                  │   │       └── test_patient.py
    │   └── project/                  │   ├── application/
    │       ├── errors.py             │   │   └── project/
    │       └── project_repository.py │   │       └── test_project_repository.py
    ├── infrastructure/               │   └── infrastructure/
    │   ├── app/                      │       ├── app/
    │   │   └── app_path_resolver.py  │       │   └── test_app_path_resolver.py
    │   └── project/                  │       └── project/
    │       └── project_path_...py    │           └── test_project_path_...py
    └── ui/                           ├── integration/
        ├── editors/                  │   └── ui/
        └── workspace/                │       └── workspace/
                                      └── data/
                                          └── fixtures/


Rule: a file foo.py in src/ has a corresponding test_foo.py in tests/ at the same relative path. A source file without a corresponding test file is a visible gap.

## 4. Levels
### 4.1 Unit tests

* **Location**: tests/unit/
* **Scope:** a single isolated unit — a function, a class, a value object. No Qt, no I/O, no filesystem.
* **Characteristics**: fast (milliseconds), independent, deterministic.

Examples:

* **test_project_id.py**: rejects empty values, equality by value, hashability.
* **test_layout_tree.py**: LayoutTree.from_specs builds the correct tree from a list of AreaSpec.
* **test_patient_identity.py**: rejects whitespace-only full_name, accepts photo_reference=None.

### 4.2 Widget tests
**Location**: tests/integration/ui/

**Scope**: the behavior of an isolated Qt widget.

**Characteristics**: use qtbot (which manages QApplication), slightly slower than unit tests.

Examples:

* test_area_widget.py: empty area shows placeholder, multi-editor area shows tabs, active_editor_changed is emitted on tab switch.
* test_toolbar.py: clicking an action emits tool_triggered, toggling a ToggleTool changes state.

### 4.3 Integration tests
Location**: tests/integration/**

**Scope**: the interaction between multiple components.

**Characteristics**: combine two or three real components, frequently use qtbot, test the observable behavior of the system.

Examples:

* test_layout_builder.py: ModuleUISpec → LayoutBuilder.build() → BuildResult, including editor creation via EditorRegistry and tree construction.
* test_workspace.py: load_spec materializes everything, clear removes everything, overlays are repositioned on layout change.

## 5. Layer coverage
Tests follow the architectural boundaries:

    Layer	            Location	                                    What is validated
    Domain	            tests/unit/domain/	                            Domain invariants (ProjectId non-empty, ProjectMetadata timezone ordering, cross-section rules in Patient)
    Application	        tests/unit/application/	                        Application contracts (ProjectRepository Protocol, EventBus dispatch)
    Infrastructure	    tests/unit/infrastructure/	                    Adapter behavior (AppPathResolver, ProjectPathResolver), using tmp_path
    UI	                tests/unit/ui/ and tests/integration/ui/	    Widget behavior, layout composition, registry behavior
    UI                  tests are the only tests that require QApplication. Any test that imports Qt is considered UI. Any test that does not can run in any environment.

## 6. Fixtures
Shared fixtures live in tests/conftest.py.

### 6.1 qapp (session-scoped)

    @pytest.fixture(scope="session")
    def qapp() -> QApplication:
        app = QApplication.instance()
        if isinstance(app, QApplication):
            return app
        return QApplication([])

Creating multiple QApplication instances breaks Qt. This fixture guarantees a single instance across the session.

### 6.2 Function-scoped fixtures
All other fixtures are function-scoped to guarantee a clean state per test:

* **Factories (make_editor, make_area)**: build objects with sensible defaults so each test declares only the fields that matter.
* **Registries (tool_registry, theme_service)**: pre-populated with default tools and services.
* **Environment (workspace, area_manager)**: a functional instance ready for use.

### 6.3 Temporary filesystem
Tests that touch the filesystem use tmp_path (provided by pytest). No test touches the user's real home directory or real projects.

## 7. Test conventions
### 7.1 Arrange-Act-Assert
Tests follow three explicit sections, separated by blank lines:

    def test_patient_age_with_birthday_already_occurred() -> None:
        # Arrange
        patient = _patient(birth_date=date(1990, 5, 12))
    
        # Act
        age = patient.age(at_date=date(2026, 6, 1))
    
        # Assert
        assert age == 36


### 7.2 One concept per test
A test name with "and" is two tests. test_load_spec_builds_areas_and_registers_overlays should be split into test_load_spec_builds_areas and test_load_spec_registers_overlays. If one fails, the failure should point directly at the broken behavior.

### 7.3 Test the contract, not the implementation
A test must survive refactoring of private methods. It must break when the public contract changes.

Tests do not import or inspect private attributes of the code under test. When a private attribute is referenced (for example, to verify that two extras dicts are distinct instances), the test explicitly documents the intent:


    # We reach into the private attribute only in the test to prove
    # the invariant; production code never does this.
    extras_a = a.persistent_state()["extras"]
    extras_b = b.persistent_state()["extras"]
    assert extras_a is not extras_b

### 7.4 Determinism
time.sleep() is prohibited. Asynchronous behavior is tested with qtbot.waitSignal or qtbot.wait. No test depends on the system clock, the network, the order of test execution, or global state shared between tests.

### 7.5 Frozen value objects
Tests verify immutability using setattr with a variable attribute name, not with direct assignment:


    def test_project_id_is_frozen() -> None:
        pid = ProjectId("abc")
        attr = "value"
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(pid, attr, "other")
This pattern satisfies both mypy (which would reject direct assignment to a frozen attribute) and ruff (which rejects setattr with a constant attribute name, B010).

## 8. Contract tests
Protocols (e.g., ProjectRepository) are not concrete classes and cannot be instantiated. To validate the contract, the tests define an in-memory reference implementation that satisfies the Protocol and exercises every documented rule.

Examples:

* ProjectRepository is a Protocol. InMemoryProjectRepository is the reference implementation. test_project_repository.py validates the contract against it: create raises ProjectAlreadyExists, get raises ProjectNotFound, list_metadata returns ProjectSummary (not Project), etc.
* When the concrete implementation (FilesystemProjectRepository) is written, it is validated against the same contract tests. If it passes, it satisfies the Protocol.

This is called a contract test: the test defines the expected behavior of any implementation, and every implementation is validated against it.

## 9. Coverage
Coverage is measured with pytest-cov but is not pursued uniformly.

    Layer	                    Coverage target	                Rationale
    Domain	                    High (>90%)	                    Dense pure logic, invariants, cross-section rules
    Application	                High	                        Orchestration and contracts
    Infrastructure	            Selective	                    Adapters, filesystem boundaries, error translation
    UI (widgets)	            Integration-focused	            Widgets that compose other widgets; pixel-level assertions are out of scope
    UI (workspace composition)	Integration-focused	            Layout composition, editor/area lifecycle

Rule: if a behavior can be described in a sentence, it must have a test. Examples:

* "PatientId rejects empty values." → test.
* "LayoutBuilder creates editors from editor_ids." → test.
* "The toolbar button is left-aligned." → not a test; design.

## 10. Out of scope
The following are intentionally not covered:

* Visual design. Colors, spacing, alignment. No pixel-level tests.
* Performance. pytest-benchmark measures specific hot paths; results are reviewed manually, not asserted.
* External libraries. DICOM, VTK, OCCT, CGAL are tested upstream. CranioZ tests the adapters that wrap them.
* Configuration content. ConfigurationLoader validates structure. The content of app.json, paths.json is reviewed manually.
* Public API stability. The project is in active development. API stability tests will be introduced when external plugins exist.

## 11. Definition of done
A piece is considered tested when:

* Every public behavior has a corresponding test.
* The tests cover the documented invariants.
* ruff format --check . passes.
* ruff check . passes.
* mypy src passes.
* pytest -q passes.
* No time.sleep() in the test suite.
* No flaky tests.
* No shared state between tests.
* 
A piece does not move to the next until these conditions hold.

## 12. Why this matters
CranioZ handles clinical data. A bug that corrupts a project can mean hours or days of lost surgical planning. A bug that miscalculates an osteotomy can mean a poorly planned surgery.

The tests are the primary defense against regressions that affect clinicians and patients. A well-tested domain (Project, Patient, Scene) is the foundation on which the rest of the system — UI, flows, plugins — can evolve with confidence.

The question is not whether coverage is 100%. It is whether the critical behaviors are protected. In CranioZ, that answer is built piece by piece, block by block.

text

---

## Passo 3 — Validar

O arquivo é Markdown puro, sem código Python, então `ruff`, `mypy` e `pytest` não são afetados. Mas vale confirmar que nada quebrou:

```bash
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m mypy src
.venv\Scripts\python.exe -m pytest -q
Esperado: tudo verde, 620 passed.
```
#### Passo 4 — Commit

    git status
    git add docs/developer/testing.md
    git commit -m "docs(developer): add testing guide"
    git log --oneline -3
    Mensagem sugerida:


    docs(developer): add testing guide
    
    - Document tools (pytest, pytest-qt, ruff, mypy)
      - Document test structure (mirrors src/)
      - Document levels (unit, widget, integration)
      - Document layer coverage
      - Document fixtures and conventions
      - Document contract tests and out-of-scope items
      - Document definition of done
