"""Scene CommandHandlers.

Each Handler:
1. Validates the Command (delegated to the domain).
2. Mutates the Scene.
3. Publishes events (delegated to CommandExecutor, which publishes
   after commit).

For the first version, the Handlers receive the Scene directly. A
future version will use a SceneRepository (Project-scoped).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from cranioz.application.scene.commands.scene_commands import (
    AddObjectToSceneCommand,
    AddRelationshipCommand,
    ImportDicomSeriesCommand,
    RemoveObjectFromSceneCommand,
    SetParentCommand,
    TransformObjectCommand,
)
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.domain.scene.scene import Scene
from cranioz.infrastructure.imaging.dicom.dicom_series_reader import (
    DicomSeriesReader,
    DicomSeriesReaderError,
)

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SceneObjectAdded:
    """A new object has been added to the Scene.

    This event is published by the CommandExecutor *after* the
    transaction commits (ADR-0007 §2.4). The Handler does not
    publish directly.
    """

    scene_id: str
    object_id: str
    kind: str


class AddObjectToSceneHandler:
    def __init__(self, scene: Scene) -> None:
        self._scene = scene

    def handle(self, command: AddObjectToSceneCommand) -> None:
        self._scene.add_object(command.object_id)


class RemoveObjectFromSceneHandler:
    def __init__(self, scene: Scene) -> None:
        self._scene = scene

    def handle(self, command: RemoveObjectFromSceneCommand) -> None:
        self._scene.remove_object(command.object_id)


class SetParentHandler:
    def __init__(self, scene: Scene) -> None:
        self._scene = scene

    def handle(self, command: SetParentCommand) -> None:
        self._scene.set_parent(command.child_id, command.parent_id)


class TransformObjectHandler:
    def __init__(self, scene: Scene) -> None:
        self._scene = scene

    def handle(self, command: TransformObjectCommand) -> None:
        self._scene.set_transform(command.object_id, command.transform)


class AddRelationshipHandler:
    def __init__(self, scene: Scene) -> None:
        self._scene = scene

    def handle(self, command: AddRelationshipCommand) -> None:
        self._scene.add_relationship(command.relationship)


class ImportDicomSeriesHandler:
    """Import a DICOM series and add the resulting Volume to the Scene.

    The handler:
    1. Uses `DicomSeriesReader` to load, validate, sort, calibrate,
       and assemble the series into a `Volume`.
    2. Registers the `Volume` in the `DomainObjectStore`.
    3. Adds the `Volume` ID to the `Scene`.

    The handler does NOT publish events. The `CommandExecutor` is
    responsible for publishing post-commit events (ADR-0007 §2.4).

    The handler does NOT open a transaction. The executor does.
    """

    def __init__(
        self,
        scene: Scene,
        object_store: DomainObjectStore,
        reader: DicomSeriesReader | None = None,
    ) -> None:
        self._scene = scene
        self._object_store = object_store
        self._reader = reader if reader is not None else DicomSeriesReader()

    def handle(self, command: ImportDicomSeriesCommand) -> None:
        path = Path(command.path)
        try:
            volume, report = self._reader.read(path)
        except DicomSeriesReaderError as exc:
            raise RuntimeError(f"cannot import DICOM series from {path}: {exc}") from exc

        if not report.success:
            raise RuntimeError(f"DICOM import failed for {path}: {report.summary()}")

        self._object_store.add(command.object_id, volume)
        self._scene.add_object(command.object_id)

        _logger.info(
            "Imported DICOM series from %s as %s: %s",
            path,
            command.object_id,
            report.summary(),
        )
