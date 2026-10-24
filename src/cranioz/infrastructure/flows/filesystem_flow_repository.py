"""FilesystemFlowRepository — filesystem adapter for FlowRepository.

Reads ``<flows_root>/<flow_id>/flow.json``. Skips corrupted entries in
``list_summaries`` and ``list_ids``; logs them. Translates all I/O
errors into ``FlowCorrupted`` / ``FlowError``. Does not write. (Seeding
is done by ``scripts/seed_flows.py``.)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from cranioz.application.flows.definition import FlowDefinition
from cranioz.application.flows.errors import (
    FlowCorrupted,
    FlowNotFound,
    FlowStorageError,
)
from cranioz.application.flows.summary import FlowSummary
from cranioz.infrastructure.flows.flow_path_resolver import (
    FLOW_FILE_NAME,
    FlowPathInaccessible,
    FlowPathResolver,
)
from cranioz.infrastructure.flows.flow_serialization import (
    FlowSerializationError,
    flow_from_dict,
)

_logger = logging.getLogger(__name__)


class FilesystemFlowRepository:
    """Filesystem-backed implementation of ``FlowRepository``."""

    def __init__(self, flows_root: Path) -> None:
        self._flows_root = Path(flows_root)

    def list_summaries(self) -> tuple[FlowSummary, ...]:
        summaries: list[FlowSummary] = []
        for flow_id in self.list_ids():
            try:
                flow = self.get(flow_id)
            except (FlowCorrupted, FlowNotFound, FlowStorageError) as exc:
                _logger.warning("skipping flow %r: %s", flow_id, exc)
                continue
            summaries.append(FlowSummary.from_definition(flow))
        return tuple(summaries)

    def list_ids(self) -> tuple[str, ...]:
        if not self._flows_root.is_dir():
            return ()
        try:
            entries = list(self._flows_root.iterdir())
        except OSError as exc:
            raise FlowStorageError(f"cannot list flows root: {self._flows_root}: {exc}") from exc

        ids: list[str] = []
        for entry in entries:
            if not entry.is_dir():
                continue
            if not (entry / FLOW_FILE_NAME).is_file():
                continue
            ids.append(entry.name)
        return tuple(ids)

    def get(self, flow_id: str) -> FlowDefinition:
        resolver = self._resolver_for(flow_id)
        if not resolver.flow_file.is_file():
            raise FlowNotFound(f"flow not found: {flow_id!r}", flow_id=flow_id)
        data = self._read_json(resolver.flow_file, flow_id)
        try:
            return flow_from_dict(data)
        except FlowSerializationError as exc:
            raise FlowCorrupted(
                f"flow is corrupted: {flow_id!r}: {exc}",
                flow_id=flow_id,
            ) from exc

    def exists(self, flow_id: str) -> bool:
        try:
            resolver = self._resolver_for(flow_id)
        except FlowStorageError:
            return False
        return resolver.flow_file.is_file()

    def _resolver_for(self, flow_id: str) -> FlowPathResolver:
        try:
            return FlowPathResolver(flows_root=self._flows_root, flow_id=flow_id)
        except FlowPathInaccessible as exc:
            raise FlowStorageError(f"invalid flow_id: {flow_id!r}: {exc}", flow_id=flow_id) from exc

    def _read_json(self, path: Path, flow_id: str) -> dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise FlowCorrupted(f"invalid JSON in {path}: {exc}", flow_id=flow_id) from exc
        except OSError as exc:
            raise FlowStorageError(f"cannot read {path}: {exc}", flow_id=flow_id) from exc
        if not isinstance(data, dict):
            raise FlowCorrupted(
                f"flow file must be a JSON object: {path}",
                flow_id=flow_id,
            )
        return data
