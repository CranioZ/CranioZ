"""Tests for FlowDefinition and FlowStep."""

from __future__ import annotations

import dataclasses

import pytest

from cranioz.application.flows.definition import (
    FlowDefinition,
    FlowStep,
)


def _step(step_id: str = "s1", module_id: str = "m1") -> FlowStep:
    return FlowStep(
        step_id=step_id,
        name_key=f"steps.{step_id}",
        module_id=module_id,
    )


def _flow(
    flow_id: str = "f1",
    steps: tuple[FlowStep, ...] = (_step(),),
) -> FlowDefinition:
    return FlowDefinition(
        flow_id=flow_id,
        name_key=f"flows.{flow_id}",
        version=1,
        steps=steps,
    )


def test_step_holds_fields() -> None:
    s = _step("patient", "patient_module")
    assert s.step_id == "patient"
    assert s.name_key == "steps.patient"
    assert s.module_id == "patient_module"


def test_step_is_frozen() -> None:
    s = _step()
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.step_id = "x"  # type: ignore[misc]


def test_empty_step_id_raises() -> None:
    with pytest.raises(ValueError, match="step_id"):
        FlowStep(step_id="", name_key="x", module_id="m")


def test_empty_name_key_raises() -> None:
    with pytest.raises(ValueError, match="name_key"):
        FlowStep(step_id="s", name_key="", module_id="m")


def test_empty_module_id_raises() -> None:
    with pytest.raises(ValueError, match="module_id"):
        FlowStep(step_id="s", name_key="k", module_id="")


def test_flow_holds_fields() -> None:
    f = _flow()
    assert f.flow_id == "f1"
    assert f.name_key == "flows.f1"
    assert f.version == 1
    assert len(f.steps) == 1


def test_flow_is_frozen() -> None:
    f = _flow()
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.flow_id = "x"  # type: ignore[misc]


def test_empty_flow_id_raises() -> None:
    with pytest.raises(ValueError, match="flow_id"):
        FlowDefinition(flow_id="", name_key="k", version=1, steps=(_step(),))


def test_version_zero_raises() -> None:
    with pytest.raises(ValueError, match="version"):
        FlowDefinition(
            flow_id="f", name_key="k", version=0, steps=(_step(),)
        )


def test_empty_steps_raises() -> None:
    with pytest.raises(ValueError, match="steps must not be empty"):
        FlowDefinition(flow_id="f", name_key="k", version=1, steps=())


def test_duplicate_step_ids_raises() -> None:
    with pytest.raises(ValueError, match="unique"):
        FlowDefinition(
            flow_id="f",
            name_key="k",
            version=1,
            steps=(_step("s1"), _step("s1")),
        )


def test_step_count() -> None:
    f = _flow(steps=(_step("s1"), _step("s2"), _step("s3")))
    assert f.step_count() == 3
