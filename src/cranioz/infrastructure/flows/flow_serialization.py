"""Serialization of FlowDefinition to/from JSON-compatible dicts.

Pure functions. No I/O. The shape is the same as the ``flow.json``
described in ``clinical_workflows.md`` §5, with the fields currently
supported by the domain (no ``icon_key`` yet; that field is added in a
later piece without breaking these JSONs).
"""

from __future__ import annotations

from typing import Any

from cranioz.application.flows.definition import (
    FlowDefinition,
    FlowStep,
)

CURRENT_SCHEMA_VERSION = 1


class FlowSerializationError(ValueError):
    """Raised when a dict cannot be interpreted as a valid FlowDefinition."""


def flow_to_dict(flow: FlowDefinition) -> dict[str, Any]:
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "flow_id": flow.flow_id,
        "name_key": flow.name_key,
        "version": flow.version,
        "steps": [
            {
                "step_id": s.step_id,
                "name_key": s.name_key,
                "module_id": s.module_id,
            }
            for s in flow.steps
        ],
    }


def flow_from_dict(data: dict[str, Any]) -> FlowDefinition:
    if not isinstance(data, dict):
        raise FlowSerializationError(f"flow data must be a dict, got {type(data).__name__}")

    schema_version = _require_int(data, "schema_version")
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise FlowSerializationError(
            f"unsupported schema_version: {schema_version} (expected {CURRENT_SCHEMA_VERSION})"
        )

    raw_steps = data.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise FlowSerializationError("flow data must have a non-empty 'steps' list")

    steps: list[FlowStep] = []
    for i, raw in enumerate(raw_steps):
        if not isinstance(raw, dict):
            raise FlowSerializationError(f"steps[{i}] must be a dict, got {type(raw).__name__}")
        try:
            step = FlowStep(
                step_id=_require_str(raw, "step_id"),
                name_key=_require_str(raw, "name_key"),
                module_id=_require_str(raw, "module_id"),
            )
        except FlowSerializationError:
            raise
        except Exception as exc:
            raise FlowSerializationError(f"invalid steps[{i}]: {exc}") from exc
        steps.append(step)

    try:
        return FlowDefinition(
            flow_id=_require_str(data, "flow_id"),
            name_key=_require_str(data, "name_key"),
            version=_require_int(data, "version"),
            steps=tuple(steps),
        )
    except FlowSerializationError:
        raise
    except Exception as exc:
        raise FlowSerializationError(f"invalid flow: {exc}") from exc


def _require_str(data: dict[str, Any], key: str) -> str:
    if key not in data:
        raise FlowSerializationError(f"missing required key: {key!r}")
    value = data[key]
    if not isinstance(value, str):
        raise FlowSerializationError(
            f"invalid type for {key!r}: expected str, got {type(value).__name__}"
        )
    return value


def _require_int(data: dict[str, Any], key: str) -> int:
    if key not in data:
        raise FlowSerializationError(f"missing required key: {key!r}")
    value = data[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise FlowSerializationError(
            f"invalid type for {key!r}: expected int, got {type(value).__name__}"
        )
    return value
