"""Seed the flows root with example flow.json files.

Development tool. Not part of production.

Creates 3 flows under ``<flows_root>/<flow_id>/flow.json``:

- orthognathic_basic
- orthognathic_advanced
- facial_implants

Idempotent: if ``flow.json`` already exists for a flow, it is skipped.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cranioz.config.loader import ConfigurationLoader
from cranioz.infrastructure.app.app_path_resolver import AppPathResolver


def _step(step_id: str, module_id: str, flow_id: str) -> dict:
    return {
        "step_id": step_id,
        "name_key": f"flows.{flow_id}.steps.{step_id}",
        "module_id": module_id,
    }


def _build_flows() -> dict[str, dict]:
    basic_steps = [
        _step("organize_data", "patient", "orthognathic_basic"),
        _step("osteotomy", "osteotomies", "orthognathic_basic"),
        _step("guide", "orthognathic_guide", "orthognathic_basic"),
    ]
    advanced_steps = [
        _step("patient", "patient", "orthognathic_advanced"),
        _step("tomography", "tomography", "orthognathic_advanced"),
        _step("cephalometry", "cephalometry", "orthognathic_advanced"),
        _step("registration", "alignment", "orthognathic_advanced"),
        _step("osteotomy", "osteotomies", "orthognathic_advanced"),
    ]
    implants_steps = [
        _step("patient", "patient", "facial_implants"),
        _step("tomography", "tomography", "facial_implants"),
        _step("implants", "orthognathic_guide", "facial_implants"),
        _step("splint", "osteotomies", "facial_implants"),
    ]
    return {
        "orthognathic_basic": {
            "schema_version": 1,
            "flow_id": "orthognathic_basic",
            "name_key": "flows.orthognathic_basic.name",
            "version": 1,
            "steps": basic_steps,
        },
        "orthognathic_advanced": {
            "schema_version": 1,
            "flow_id": "orthognathic_advanced",
            "name_key": "flows.orthognathic_advanced.name",
            "version": 1,
            "steps": advanced_steps,
        },
        "facial_implants": {
            "schema_version": 1,
            "flow_id": "facial_implants",
            "name_key": "flows.facial_implants.name",
            "version": 1,
            "steps": implants_steps,
        },
    }


def _flows_root() -> Path:
    config = ConfigurationLoader().load()
    app_paths = AppPathResolver()
    app_paths.initialize(config.paths)
    return app_paths.flows_root


def main() -> int:
    root = _flows_root()
    print(f"Flows root: {root}")

    flows = _build_flows()
    created = 0
    skipped = 0
    for flow_id, data in flows.items():
        flow_dir = root / flow_id
        flow_file = flow_dir / "flow.json"
        if flow_file.is_file():
            print(f"  skip   {flow_id!r} - already exists")
            skipped += 1
            continue
        flow_dir.mkdir(parents=True, exist_ok=True)
        with flow_file.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"  create {flow_id!r}")
        created += 1

    print(f"\nDone. Created: {created}, skipped: {skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
