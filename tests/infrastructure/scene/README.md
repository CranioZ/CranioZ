# Unit tests - infrastructure/scene

**Status:** Contract reserved, test not yet implemented.

`test_scene_query_adapter.py` is **intentionally empty**. It reserves
the unit-test contract for
`src/cranioz/infrastructure/scene/scene_query_adapter.py`.

## Why it exists

`InfrastructureSceneQueryAdapter` is consumed by `MainWindow` (see
`main_window.py::_create_workspace`) and covered indirectly through
integration tests. The unit contract (adapter delegates to the
underlying `Scene`, respects the query interface, handles empty
results) is not yet isolated.

## How to implement

1. Remove the `# TODO(sprint-scene)` marker.
2. Write focused tests against an in-memory `Scene` fake.
3. Do not duplicate the integration coverage.

## References

- `Implementation Plan.md` section 3.3.5
- `Consolidation Plan` section 7.3