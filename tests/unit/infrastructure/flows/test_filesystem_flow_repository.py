"""Tests for FilesystemFlowRepository."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cranioz.application.flows.errors import (
    FlowCorrupted,
    FlowNotFound,
)
from cranioz.application.flows.repository import FlowRepository
from cranioz.infrastructure.flows.filesystem_flow_repository import (
    FilesystemFlowRepository,
    FlowStorageError,
)

_VALID_FLOW = {
    "schema_version": 1,
    "flow_id": "orthognathic",
    "name_key": "flows.orthognathic.name",
    "version": 1,
    "steps": [
        {"step_id": "patient", "name_key": "steps.patient", "module_id": "patient"},
        {"step_id": "osteotomy", "name_key": "steps.osteotomy", "module_id": "osteotomies"},
    ],
}


@pytest.fixture
def root(tmp_path: Path) -> Path:
    flows = tmp_path / "flows"
    flows.mkdir()
    return flows


@pytest.fixture
def repo(root: Path) -> FilesystemFlowRepository:
    return FilesystemFlowRepository(flows_root=root)


def _write_flow(
    root: Path,
    flow_id: str,
    data: dict | None = None,
) -> None:
    d = root / flow_id
    d.mkdir(parents=True, exist_ok=True)
    if data is None:
        # Copy the valid template and override flow_id.
        data = dict(_VALID_FLOW)
        data["flow_id"] = flow_id
    (d / "flow.json").write_text(json.dumps(data), encoding="utf-8")


def test_satisfies_protocol(repo: FilesystemFlowRepository) -> None:
    assert isinstance(repo, FlowRepository)


def test_empty(repo: FilesystemFlowRepository) -> None:
    assert repo.list_summaries() == ()
    assert repo.list_ids() == ()


def test_get_valid(repo: FilesystemFlowRepository, root: Path) -> None:
    _write_flow(root, "orthognathic")
    flow = repo.get("orthognathic")
    assert flow.flow_id == "orthognathic"
    assert flow.step_count() == 2


def test_get_missing(repo: FilesystemFlowRepository) -> None:
    with pytest.raises(FlowNotFound):
        repo.get("unknown")


def test_get_corrupted(repo: FilesystemFlowRepository, root: Path) -> None:
    d = root / "bad"
    d.mkdir()
    (d / "flow.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(FlowCorrupted):
        repo.get("bad")


def test_list_ids(repo: FilesystemFlowRepository, root: Path) -> None:
    _write_flow(root, "a")
    _write_flow(root, "b")
    (root / "stray").mkdir()  # no flow.json
    assert set(repo.list_ids()) == {"a", "b"}


def test_list_summaries(repo: FilesystemFlowRepository, root: Path) -> None:
    _write_flow(root, "a")
    _write_flow(root, "b")
    summaries = repo.list_summaries()
    assert len(summaries) == 2
    assert {s.flow_id for s in summaries} == {"a", "b"}


def test_list_summaries_skips_corrupted(repo: FilesystemFlowRepository, root: Path) -> None:
    _write_flow(root, "ok")
    d = root / "bad"
    d.mkdir()
    (d / "flow.json").write_text("{", encoding="utf-8")
    summaries = repo.list_summaries()
    assert len(summaries) == 1
    assert summaries[0].flow_id == "ok"


def test_exists_true(repo: FilesystemFlowRepository, root: Path) -> None:
    _write_flow(root, "a")
    assert repo.exists("a") is True


def test_exists_false(repo: FilesystemFlowRepository) -> None:
    assert repo.exists("unknown") is False


def test_invalid_flow_id_raises_storage_error(
    repo: FilesystemFlowRepository,
) -> None:
    with pytest.raises(FlowStorageError):
        repo.get("a/b")
