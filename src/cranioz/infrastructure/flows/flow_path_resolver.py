"""FlowPathResolver — resolves file paths inside a flow directory.

Analogous to ``ProjectPathResolver``. The resolver is built with two
pieces of information:

- the flows root (``AppPathResolver.flows_root``);
- the ``flow_id`` of the flow being opened.

From those, it derives ``<flows_root>/<flow_id>/flow.json``.

It does not touch the filesystem beyond ``exists()``. It validates
the ``flow_id`` as a safe single path segment (rejects ``/``, ``\\``,
``..``, ``:``, control characters, and leading dots).
"""

from __future__ import annotations

from pathlib import Path

FLOW_FILE_NAME = "flow.json"


class FlowPathInaccessible(Exception):
    """Raised when a flow path cannot be resolved."""


class FlowPathResolver:
    """Resolves file paths inside a specific flow directory."""

    def __init__(self, flows_root: Path, flow_id: str) -> None:
        self._validate_flow_id(flow_id)
        self._flows_root = flows_root
        self._flow_id = flow_id

    @property
    def flows_root(self) -> Path:
        return self._flows_root

    @property
    def flow_id(self) -> str:
        return self._flow_id

    @property
    def flow_dir(self) -> Path:
        return self._flows_root / self._flow_id

    @property
    def flow_file(self) -> Path:
        return self.flow_dir / FLOW_FILE_NAME

    def exists(self) -> bool:
        return self.flow_dir.is_dir()

    @staticmethod
    def _validate_flow_id(flow_id: str) -> None:
        if not flow_id or not flow_id.strip():
            raise FlowPathInaccessible("FlowId value must not be empty or whitespace only")
        if "/" in flow_id or "\\" in flow_id:
            raise FlowPathInaccessible(
                f"FlowId value must not contain path separators: {flow_id!r}"
            )
        if ".." in flow_id:
            raise FlowPathInaccessible(f"FlowId value must not contain '..': {flow_id!r}")
        if ":" in flow_id:
            raise FlowPathInaccessible(f"FlowId value must not contain ':': {flow_id!r}")
        if any(ord(ch) < 0x20 for ch in flow_id):
            raise FlowPathInaccessible(
                f"FlowId value must not contain control characters: {flow_id!r}"
            )
        if flow_id.startswith("."):
            raise FlowPathInaccessible(f"FlowId value must not start with '.': {flow_id!r}")
