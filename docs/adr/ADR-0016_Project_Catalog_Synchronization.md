# ADR-0016 — Project Catalog Synchronization

**Status:** Accepted
**Date:** 2026-11-18
**Supersedes:** —
**Related:** `project.md` §6, §22; `implementation_plan.md` Sprint I; `next_steps.md` §5.1; ADR-0004 (paths), ADR-0015 (Editor/Module reorganization)
**Sprint:** I (ProjectIndex)

---

## 1. Context

The `ProjectCatalog` is a read-only discovery projection consumed by the Home Page (`project.md` §5, §7; `homepage.md` §6). It answers *"which projects exist and what do they look like?"* without loading clinical data.

Until 2026-11-18, the catalog delegated every query to `ProjectRepository.list_metadata()`. `FilesystemProjectRepository.list_metadata()` performs, for each project, one directory entry probe, one `json.load`, one `project_from_dict`, and one `ProjectSummary.from_metadata` — that is, **N filesystem reads and N JSON decodes per query**, where N is the number of persisted projects.

`ProjectCatalog` invokes `list_metadata()` multiple times per logical operation:

| Operation | Reads |
|---|---|
| `list_projects()` | 1× N |
| `get_project_summary(id)` | 1× N |
| `search_projects(query)` | 1× N |
| `count()` | 1× N |
| `is_empty()` | 1× N |
| `contains(id)` | 1× N |

The Home Page's `ProjectTable` triggers `search_projects()` on each keystroke. With N projects and a K-character query, the cost is O(N·K) filesystem operations. On local SSD with a handful of projects this is imperceptible; with 300 projects on a network path (`Homepage.md` §12 explicitly anticipates `D:\ClinicalData\...`), it is a structural inefficiency that is avoidable by design.

`project.md` §6 authorizes this decision explicitly:

> The synchronization mechanism is intentionally not fixed by this document. Possible mechanisms include: application/domain events; explicit catalog invalidation; repository-backed refresh; controlled cache invalidation; other deterministic synchronization mechanisms. […] The precise synchronization strategy should be defined in a dedicated ADR, such as `adr/project-catalog-synchronization.md`.

This ADR is that decision. It also cites the `ProjectCatalog`'s own documented anticipation:

> If future profiling shows the catalog is a hot path, a cache will be added in a separate piece, explicitly invalidated by subscribing to `ProjectCreated` / `ProjectUpdated` / `ProjectDeleted`. Until then: no cache.

The Sprint I condition is now met: the cost has been demonstrated structurally.

---

## 2. Decision

The `ProjectCatalog` consumes a `ProjectIndex` — a read-only, in-memory projection of `ProjectSummary` values — populated by a `ProjectIndexSynchronizer` that performs an initial repository-backed bootstrap and maintains the projection via application lifecycle events.

### 2.1 Component responsibilities

| Component | Layer | Responsibility |
|---|---|---|
| `ProjectIndex` (Protocol) | Application | Pure read model: `add`, `remove`, `lookup`, `list_summaries`, `list_ids`, `count`, `contains`, `replace_all`. No I/O. No knowledge of repository or events. |
| `InMemoryProjectIndex` | Application | Reference implementation: a dict keyed by `ProjectId`. |
| `ProjectIndexSynchronizer` | Application | Bootstrap (subscribe → repository read → `replace_all`), subscribe to `ProjectCreated`/`ProjectUpdated`/`ProjectDeleted`, apply incremental updates, mark `_possibly_stale` on handler failure, `rebuild()`, `ensure_fresh()`, `start()`. |
| `SynchronizedProjectIndex` | Application | Decorator implementing `ProjectIndex`. Delegates every read to the inner index after calling `synchronizer.ensure_fresh()`. |
| `ProjectCatalog` | Application | Consumes `ProjectIndex` only. No knowledge of the synchronizer. |
| `ProjectRepository` | Port | Unchanged. Authoritative persistence. |
| `FilesystemProjectRepository` | Infrastructure | Unchanged. The only filesystem reader. |

### 2.2 Data flow

**Bootstrap (once, at composition root):**

    ProjectIndexSynchronizer.start()
    → event_bus.subscribe(ProjectCreated, self._on_created)
    → event_bus.subscribe(ProjectUpdated, self._on_updated)
    → event_bus.subscribe(ProjectDeleted, self._on_deleted)
    → summaries = repository.list_metadata()
    → index.replace_all(summaries)

**Query (Home Page):**

    ProjectCatalog.list_projects()
    → SynchronizedProjectIndex.list_summaries()
    → synchronizer.ensure_fresh() # no-op if not stale; rebuild if stale
    → inner.list_summaries() # in-memory, zero I/O


**Mutation (ProjectManager):**

    manager.create_project(...)
    → repository.create(project) # persists
    → event_bus.publish(ProjectCreated(...))
    → synchronizer._on_created(event)
    → index.add(ProjectSummary.from_metadata(event.metadata))
    → on failure: log + _possibly_stale = True; do not propagate
    → manager returns success


---

## 3. Consistency contract

### 3.1 Guarantee

After `ProjectManager.create_project`, `update_project`, or `delete_project` returns successfully **and the corresponding event has been dispatched synchronously**, the next query to the catalog reflects the mutation.

This is guaranteed because:

- `EventBus.publish` is synchronous and single-threaded (documented in `event_bus.py`).
- `ProjectManager` publishes **after** the repository operation succeeds.
- The synchronizer handler updates the index synchronously within `publish`.
- `ProjectManager` returns only after `publish` returns.

### 3.2 Explicit non-coverage

The following are **not** detected automatically:

- Manual edits to `project.json` outside the application.
- Another process modifying the projects directory.
- Restoring a backup over a project.

These require an explicit `ProjectIndexSynchronizer.rebuild()` or an application restart. **Background disk reconciliation** is deferred to Phase 8 (`implementation_plan.md` §6, "Background disk reconciliation").

### 3.3 Staleness rule

> **A query must never silently return data from a stale index.**

`_possibly_stale` is set on the synchronizer when:

- An event handler fails to update the index (`index.add`, `index.remove`, or `index.replace_all` raises).

The next call to `SynchronizedProjectIndex` invokes `synchronizer.ensure_fresh()`:

1. If `_possibly_stale` is `False`: no-op. The query proceeds.
2. If `_possibly_stale` is `True`: `rebuild()` is invoked (`repository.list_metadata()` → `replace_all`).
   - On success: `_possibly_stale = False`; the query proceeds with fresh data.
   - On failure: `ProjectIndexStaleError` is raised. The query does **not** return stale data.

`ProjectIndexStaleError` is an application-level error (`application/project/index.py`), distinct from `ProjectRepositoryError` family. Its user-facing message is presented by `MainWindow`, which uses the existing `QMessageBox` pattern.

### 3.4 Handler error containment

`ProjectIndexSynchronizer`'s handlers **must not propagate exceptions to the `EventBus`.** Reason: `EventBus.publish` collects handler exceptions and re-raises them as `EventBusError`; this would surface as an error in `ProjectManager.create_project`, incorrectly implying that the persistent mutation failed. Instead, handlers:

- Catch every exception.
- Log at WARNING with `project_id` and operation name only (**never** `project_name` or `patient_display_name`).
- Set `_possibly_stale = True`.
- Return normally.

---

## 4. Bootstrap ordering

The synchronizer's `start()` performs, in order, on the same synchronous call stack:

1. Subscribe to `ProjectCreated`, `ProjectUpdated`, `ProjectDeleted`.
2. `summaries = repository.list_metadata()`.
3. `index.replace_all(summaries)`.

**No event can be published between (1) and (3)** because:

- `EventBus.publish` is synchronous, single-threaded.
- `ProjectManager` runs on the same thread as the synchronizer.
- `start()` does not yield control (`await`, `processEvents()`, or blocking I/O that could re-enter the event loop) between (1) and (3).

Therefore, **no event queue is needed.** Direct ordering is sufficient.

### 4.1 Re-evaluation trigger

This decision is valid **only while the bootstrap is synchronous**. Phase 3 Sprint K (Async loading) will make `HomePage` load projects via `TaskManager`. If the index bootstrap becomes asynchronous, a publication between (1) and (3) becomes possible, and the strategy must be revisited. Options at that time: a bootstrap-time event queue, or a transactional `replace_all` that preserves concurrent `add` operations.

The ADR does not pre-commit to a solution. It records that Sprint K must re-open this decision.

---

## 5. Alternatives considered

| Alternative | Rejected because |
|---|---|
| **Keep current behavior** (catalog queries repository directly) | O(N) filesystem reads per query; O(N·K) per search keystroke; network-path cost unaddressed. |
| **TTL / polling cache** | `project.md` §6 explicitly forbids "Polling or TTL-based caching … by the Home Page itself as an independent consistency mechanism." |
| **Persisted filesystem index** (`index.json`) | Adds a second source of truth that can desynchronize from `project.json`. Deferred to Phase 8 alongside SQLite. |
| **`ProjectCatalog` depends on `ProjectIndexSynchronizer`** | Couples the read model to the maintenance mechanism. Rejected in design review: the catalog must depend only on the read contract (`ProjectIndex`). The decorator (`SynchronizedProjectIndex`) is the correct insertion point. |
| **`ProjectIndex.refresh()`** | Mixes the read model with a maintenance operation. The index only knows how to `replace_all`; knowing *when* to rebuild is the synchronizer's concern. |
| **SQLite `ProjectIndex`** | Deferred to Phase 8. The `ProjectIndex` Protocol is designed so the SQLite implementation can replace `InMemoryProjectIndex` without changing the synchronizer or the catalog. |
| **Event queue during bootstrap** | Unnecessary while bootstrap is synchronous. Re-evaluate in Sprint K. |

---

## 6. Consequences

### 6.1 Positive

- Query cost after bootstrap is **O(1)** in filesystem reads, regardless of N.
- `search_projects` on the Home Page stops issuing N reads per keystroke.
- The authoritative source (`ProjectRepository`) is unchanged.
- The read contract (`ProjectIndex`) is stable; SQLite migration in Phase 8 is contract-preserving.
- No new persisted state.
- Consistent with `project.md` §6's "repository-backed refresh" mechanism and its "no TTL, no polling" restriction.

### 6.2 Negative

- **Startup cost:** bootstrap performs one `repository.list_metadata()`. Same order as the first catalog query today; the cost is moved from "per query" to "once".
- **Staleness window on external mutation:** documented in §3.2. Mitigated by `rebuild()`, restart, and (future) background reconciliation.
- **New failure mode:** if `rebuild()` fails, queries raise `ProjectIndexStaleError`. The Home Page must present this gracefully.
- **Sprint K coupling:** if async bootstrap is introduced without revisiting §4, the initialization window re-opens.

### 6.3 Neutral

- `ProjectCatalog.refresh()` is **removed**. Freshness is automatic on every query through `SynchronizedProjectIndex`. `HomePage.refresh()` is adjusted to not call it.
- `ProjectCatalog` constructor changes from `(repository)` to `(index: ProjectIndex)`. The composition root (`__main__` / `MainWindow`) assembles `InMemoryProjectIndex` + `ProjectIndexSynchronizer` + `SynchronizedProjectIndex` + `ProjectCatalog`.
- The `ProjectIndexSynchronizer.start()` is explicit; it is called once by the composition root, not in the constructor. This makes the "not started / started / failed bootstrap" states testable.

---

## 7. Implementation summary

**Files (all under `cranioz/application/project/`, flat package — no `protocols/` subfolder, matching the existing convention of `catalog.py`, `manager.py`, `repository.py`, `errors.py`):**

| File | Contents |
|---|---|
| `index.py` | `ProjectIndex` Protocol; `ProjectIndexStaleError`. |
| `in_memory_index.py` | `InMemoryProjectIndex`. |
| `index_synchronizer.py` | `ProjectIndexSynchronizer`; `SynchronizedProjectIndex` decorator. |
| `catalog.py` | Refactored to consume `ProjectIndex`; `refresh()` removed. |

**Composition root** (`__main__.py` / `MainWindow.__init__`):

```python
index = InMemoryProjectIndex()
synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
synchronizer.start()
catalog = ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))
```
Test files:

File	Focus
test_project_index_contract.py	InMemoryProjectIndex contract; parametrizable for future SqliteProjectIndex.
test_project_index_synchronizer.py	Bootstrap, event handlers, error containment, rebuild, ensure_fresh.
test_project_index_sync_bootstrap.py	Reproduces the bootstrap window; verifies consistency.
test_project_catalog_uses_index.py	Catalog reads via ProjectIndex only; fails if repository.list_metadata is called during queries.
test_project_catalog_sync.py	End-to-end integration with ProjectManager.
test_project_index_stale_propagation.py	ProjectIndexStaleError propagation; MainWindow handling.
Benchmark (documented in this ADR's implementation notes, not run in CI): 100 / 300 / 1000 projects in tmp_path, comparing search_projects() latency and repository.list_metadata call count between baseline (direct repository) and new (indexed).

8. Verification criteria
The Sprint I is complete when:

ProjectIndex, InMemoryProjectIndex, ProjectIndexSynchronizer, and SynchronizedProjectIndex exist with contract tests.

ProjectCatalog consumes ProjectIndex; list_metadata is not called by catalog queries (verified by a mock that fails if invoked).

ProjectManager.create_project → catalog reflects the new project on the next query.

ProjectManager.update_project → catalog reflects the updated metadata.

ProjectManager.delete_project → catalog no longer lists the project.

Bootstrap ordering test passes: no event is lost when published between subscribe and replace_all under the synchronous EventBus.

Handler failure marks _possibly_stale; next query triggers rebuild; failure of rebuild raises ProjectIndexStaleError; the Home Page presents the error, not stale data.

No PHI in error logs (project_name, patient_display_name never logged).

All existing project subsystem tests pass unchanged (except tests that constructed ProjectCatalog(repository) directly, which are updated to construct ProjectCatalog(SynchronizedProjectIndex(...))).

pytest, ruff check, ruff format --check, mypy src all pass.

Benchmark recorded in the ADR's implementation notes; not a CI gate.

9. Related ADRs
ADR-0004 — application and project path resolution. ProjectRepository and ProjectIndex remain independent of physical layout.

ADR-0015 — Editor and Module package reorganization. Sprint I follows its package conventions (application/project/ flat, no protocols/ subfolder).
