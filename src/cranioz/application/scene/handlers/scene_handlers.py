"""Scene CommandHandlers.

Each Handler:
1. Validates the Command (delegated to the domain).
2. Mutates the Scene.
3. (Future) Publishes events.

For the first version, the Handlers receive the Scene directly. A
future version will use a SceneRepository (Project-scoped).
"""

from __future__ import annotations

from cranioz.application.scene.commands.scene_commands import (
    AddObjectToSceneCommand,
    AddRelationshipCommand,
    RemoveObjectFromSceneCommand,
    SetParentCommand,
    TransformObjectCommand,
)
from cranioz.domain.scene.scene import Scene


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
