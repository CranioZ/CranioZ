# Unit tests - infrastructure/i18n

**Status:** Contract reserved, tests not yet implemented.

These files are **intentionally empty stubs**. They reserve the
granular unit-test contract for `src/cranioz/infrastructure/i18n/`.

## Why they exist

End-to-end coverage for i18n already exists in `tests/integration/i18n/`
(`test_flow_catalog_translation.py`, `test_flow_fixture_parity.py`).
What is missing is **unit-level** coverage of the individual
infrastructure classes, isolated from the shell:

- `test_catalog_loader.py` -> `TranslationCatalog` JSON loading,
  malformed input, missing keys, encoding.
- `test_catalog_registry.py` -> `TranslationCatalogRegistry`
  registration, lookup, fallback to `en`, duplicate registration.
- `test_translation_service.py` -> concrete
  `CatalogTranslationService`: `tr()` fallback chain,
  `set_language`, missing-key behavior.

## How to implement

Each stub carries a `# TODO(sprint-i18n)` marker. When implementing:

1. Remove the `# TODO(sprint-i18n)` marker from the stub.
2. Write focused unit tests (no `MainWindow`, no `Workspace`, no
   shell widgets).
3. Use fixtures from `conftest.py` for a minimal in-memory catalog.
4. Keep the existing `tests/integration/i18n/` coverage intact - do
   not duplicate it.

## References

- `Implementation Plan.md` section 3.3.5
- `Consolidation Plan` section 7.3 (prevent parallel implementations)
- `Next Steps.md` section 3.3.5