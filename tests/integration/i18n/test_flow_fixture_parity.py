"""Parity test: fixtures must use the same `name_key` values as production.

This test is optional. It is skipped when the production `flows_root`
is not accessible (e.g., in CI without installed flows). When it runs,
it catches the case where a production `flow.json` adds a new step or
renames a key, but the fixture was not updated.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cranioz.config.loader import ConfigurationLoader
from cranioz.infrastructure.app.app_path_resolver import (
    AppPathInaccessible,
    AppPathResolver,
)
from cranioz.infrastructure.flows.flow_serialization import flow_from_dict

_REPO_ROOT = Path(__file__).parents[3]
_FIXTURES_ROOT = _REPO_ROOT / "tests" / "data" / "fixtures" / "flows"


def _production_flows_root() -> Path | None:
    try:
        config = ConfigurationLoader().load()
        resolver = AppPathResolver()
        resolver.initialize(config.paths, create=False)
        return resolver.flows_root
    except (AppPathInaccessible, Exception):
        return None


def _read_flow_keys(flow_file: Path) -> tuple[str, set[str]]:
    data = json.loads(flow_file.read_text(encoding="utf-8"))
    flow = flow_from_dict(data)
    keys = {flow.name_key}
    keys.update(step.name_key for step in flow.steps)
    return flow.flow_id, keys


def _collect_keys(root: Path) -> dict[str, set[str]]:
    """Return {flow_id: set(name_keys)} for every flow.json under `root`."""
    result: dict[str, set[str]] = {}
    for flow_file in sorted(root.glob("*/flow.json")):
        flow_id, keys = _read_flow_keys(flow_file)
        result[flow_id] = keys
    return result


def test_fixtures_match_production_keys() -> None:
    production_root = _production_flows_root()
    if production_root is None:
        pytest.skip("production flows_root is not accessible")

    production = _collect_keys(production_root)
    fixtures = _collect_keys(_FIXTURES_ROOT)

    missing_in_fixtures: dict[str, set[str]] = {}
    missing_in_production: dict[str, set[str]] = {}

    for flow_id, prod_keys in production.items():
        fix_keys = fixtures.get(flow_id, set())
        diff = prod_keys - fix_keys
        if diff:
            missing_in_fixtures[flow_id] = diff

    for flow_id, fix_keys in fixtures.items():
        prod_keys = production.get(flow_id, set())
        diff = fix_keys - prod_keys
        if diff:
            missing_in_production[flow_id] = diff

    assert not missing_in_fixtures, (
        f"fixtures are missing keys present in production: {missing_in_fixtures}"
    )
    assert not missing_in_production, (
        f"fixtures declare keys not present in production: {missing_in_production}"
    )
