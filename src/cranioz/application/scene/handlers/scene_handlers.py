"""Scene CommandHandlers.

Each Handler:
1. Validates the Command (delegated to the domain).
2. Mutates the Scene.
3. (Future) Publishes events.

For the first version, the Handlers receive the Scene directly. A
future version will use a SceneRepository (Project-scoped).
"""

from __future__ import annotations

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
from cranioz.infrastructure.imaging.dicom_loader import (
    load_dicom_series,
)


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
    """Load a DICOM series and add the resulting volume to the Scene.

    The handler:
    1. Loads the series via the DICOM loader (infrastructure).
    2. Registers the ``VolumeData`` in the ``DomainObjectStore``.
    3. Adds the ``object_id`` to the ``Scene``.

    The handler does **not** publish events (the ``CommandExecutor``
    is responsible for that — see ADR-0007 §2.4). It also does not
    open a transaction (the executor does).
    """

    def __init__(self, scene: Scene, object_store: DomainObjectStore) -> None:
        self._scene = scene
        self._object_store = object_store

    def handle(self, command: ImportDicomSeriesCommand) -> None:
        volume = load_dicom_series(Path(command.path))  # raises DicomLoadError
        self._object_store.add(command.object_id, volume)
        self._scene.add_object(command.object_id)
