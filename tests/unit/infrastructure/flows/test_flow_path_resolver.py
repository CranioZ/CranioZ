"""Tests for FlowPathResolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from cranioz.infrastructure.flows.flow_path_resolver import (
    FLOW_FILE_NAME,
    FlowPathInaccessible,
    FlowPathResolver,
)


def test_flow_file_name() -> None:
    assert FLOW_FILE_NAME == "flow.json"


def test_resolver_holds_root(tmp_path: Path) -> None:
    r = FlowPathResolver(flows_root=tmp_path, flow_id="abc")
    assert r.flows_root == tmp_path


def test_flow_dir(tmp_path: Path) -> None:
    r = FlowPathResolver(flows_root=tmp_path, flow_id="abc")
    assert r.flow_dir == tmp_path / "abc"


def test_flow_file(tmp_path: Path) -> None:
    r = FlowPathResolver(flows_root=tmp_path, flow_id="abc")
    assert r.flow_file == tmp_path / "abc" / "flow.json"


def test_rejects_slash(tmp_path: Path) -> None:
    with pytest.raises(FlowPathInaccessible, match="separators"):
        FlowPathResolver(flows_root=tmp_path, flow_id="a/b")


def test_rejects_backslash(tmp_path: Path) -> None:
    with pytest.raises(FlowPathInaccessible, match="separators"):
        FlowPathResolver(flows_root=tmp_path, flow_id="a\\b")


def test_rejects_dotdot(tmp_path: Path) -> None:
    with pytest.raises(FlowPathInaccessible, match=r"\.\."):
        FlowPathResolver(flows_root=tmp_path, flow_id="a..b")


def test_rejects_colon(tmp_path: Path) -> None:
    with pytest.raises(FlowPathInaccessible, match=":"):
        FlowPathResolver(flows_root=tmp_path, flow_id="a:b")


def test_rejects_leading_dot(tmp_path: Path) -> None:
    with pytest.raises(FlowPathInaccessible, match="start with"):
        FlowPathResolver(flows_root=tmp_path, flow_id=".hidden")


def test_rejects_control_char(tmp_path: Path) -> None:
    with pytest.raises(FlowPathInaccessible, match="control"):
        FlowPathResolver(flows_root=tmp_path, flow_id="a\x00b")


def test_exists_false(tmp_path: Path) -> None:
    r = FlowPathResolver(flows_root=tmp_path, flow_id="abc")
    assert r.exists() is False


def test_exists_true(tmp_path: Path) -> None:
    (tmp_path / "abc").mkdir()
    r = FlowPathResolver(flows_root=tmp_path, flow_id="abc")
    assert r.exists() is True
