"""Contract test: every name_key in every fixture flow.json resolves.

The test reads the flow definitions from `tests/data/fixtures/flows/`,
a versioned directory of canonical flow definitions. The fixtures use
exactly the same `name_key` values as the production flows, so the test
guards against the regression where a `flow.json` uses a key that the
catalog does not define.

The test verifies two things for every supported language:

1. Every `name_key` in every flow (and every step) resolves through the
   `TranslationService` — i.e., the catalog `flows.json` defines it.

2. The catalog `flows.json` does not declare keys that no fixture uses —
   i.e., the catalog stays honest, not just complete.

The authoritative source of truth is the English catalog. The test does
not check the exact translated text, only that a translation exists
(i.e., `tr(key, key) != key`). A future test may assert exact strings.

The fixtures are not production flows. They are minimal, canonical
copies that exercise the catalog. If a production `flow.json` adds a new
`name_key`, the fixture must add it too — that is the maintenance cost
of this variant. `tests/integration/i18n/test_flow_fixture_parity.py`
(optional) can compare the fixtures against the production flows when
the `flows_root` is accessible.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cranioz.application.flows.definition import FlowDefinition
from cranioz.infrastructure.flows.flow_serialization import flow_from_dict
from cranioz.infrastructure.i18n.catalog_loader import CatalogLoader
from cranioz.infrastructure.i18n.catalog_registry import (
    TranslationCatalogRegistry,
)
from cranioz.infrastructure.i18n.translation_service import (
    CatalogTranslationService,
)

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

# tests/integration/i18n/test_flow_catalog_translation.py
# parents[0] = tests/integration/i18n
# parents[1] = tests/integration
# parents[2] = tests
# parents[3] = <repo root>
_REPO_ROOT = Path(__file__).parents[3]
_FIXTURES_ROOT = _REPO_ROOT / "tests" / "data" / "fixtures" / "flows"
_TRANSLATIONS_ROOT = _REPO_ROOT / "src" / "cranioz" / "translations"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _flow_files() -> list[Path]:
    """Return every fixture `flow.json`, sorted for determinism."""
    if not _FIXTURES_ROOT.is_dir():
        pytest.skip(f"fixtures root not found: {_FIXTURES_ROOT}")
    files = sorted(_FIXTURES_ROOT.glob("*/flow.json"))
    if not files:
        pytest.skip(f"no flow.json under {_FIXTURES_ROOT}")
    return files


def _load_flow(flow_file: Path) -> FlowDefinition:
    data = json.loads(flow_file.read_text(encoding="utf-8"))
    return flow_from_dict(data)


def _make_service(language: str) -> CatalogTranslationService:
    loader = CatalogLoader(_TRANSLATIONS_ROOT)
    registry = TranslationCatalogRegistry(loader)
    return CatalogTranslationService(registry, language=language)


def _assert_resolves(
    service: CatalogTranslationService,
    key: str,
    context: str,
) -> None:
    resolved = service.tr(key, key)
    assert resolved != key, (
        f"{context}: key {key!r} did not resolve. The catalog `flows.json` is missing this key."
    )


def _declared_flow_keys() -> set[str]:
    """Return every leaf key declared under `flows.*` in `en/flows.json`.

    Walks the JSON tree and collects paths that end in an object with a
    `message` field. Skips `_metadata`. The result uses dotted paths
    starting with `flows` (e.g., `flows.orthognathic_basic.name`).
    """
    catalog_path = _TRANSLATIONS_ROOT / "en" / "flows.json"
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    declared: set[str] = set()

    def _walk(node: object, prefix: str) -> None:
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            if key == "_metadata":
                continue
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and "message" in value:
                declared.add(path)
            elif isinstance(value, dict):
                _walk(value, path)

    _walk(data, "flows")
    return declared


# ---------------------------------------------------------------------
# Fixtures (pytest)
# ---------------------------------------------------------------------


@pytest.fixture(scope="module")
def service_en() -> CatalogTranslationService:
    return _make_service("en")


@pytest.fixture(scope="module")
def service_pt() -> CatalogTranslationService:
    return _make_service("pt-BR")


# ---------------------------------------------------------------------
# Completeness: every key in the fixtures resolves in every language
# ---------------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_flow_name_keys_resolve(language: str) -> None:
    service = _make_service(language)
    for flow_file in _flow_files():
        flow = _load_flow(flow_file)
        _assert_resolves(
            service,
            flow.name_key,
            f"{flow_file} (flow name, {language})",
        )


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_step_keys_resolve(language: str) -> None:
    service = _make_service(language)
    for flow_file in _flow_files():
        flow = _load_flow(flow_file)
        for step in flow.steps:
            _assert_resolves(
                service,
                step.name_key,
                f"{flow_file} (step {step.step_id!r}, {language})",
            )


# ---------------------------------------------------------------------
# Honesty: every key declared in the catalog is used by some fixture
# ---------------------------------------------------------------------


def test_catalog_has_no_unused_flow_keys() -> None:
    used: set[str] = set()
    for flow_file in _flow_files():
        flow = _load_flow(flow_file)
        used.add(flow.name_key)
        used.update(step.name_key for step in flow.steps)

    unused = _declared_flow_keys() - used
    assert not unused, f"catalog `flows.json` has entries that no fixture uses: {sorted(unused)}"
