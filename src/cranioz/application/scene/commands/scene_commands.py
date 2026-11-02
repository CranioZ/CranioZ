"""Scene Commands — state mutations for the Scene.

Every persistent mutation of the Scene goes through a Command
(ADR-0007). The handlers are in `scene_handlers.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from cranioz.application.commands.base import Command
from cranioz.domain.scene.relationship import SpatialRelationship
from cranioz.domain.scene.transform import Transform


@dataclass(frozen=True, kw_only=True)
class AddObjectToSceneCommand(Command):
    scene_id: str
    object_id: str

    def __post_init__(self) -> None:
        if not self.scene_id:
            raise ValueError("scene_id must not be empty")
        if not self.object_id:
            raise ValueError("object_id must not be empty")


@dataclass(frozen=True, kw_only=True)
class RemoveObjectFromSceneCommand(Command):
    scene_id: str
    object_id: str


@dataclass(frozen=True, kw_only=True)
class SetParentCommand(Command):
    scene_id: str
    child_id: str
    parent_id: str


@dataclass(frozen=True, kw_only=True)
class TransformObjectCommand(Command):
    scene_id: str
    object_id: str
    transform: Transform


@dataclass(frozen=True, kw_only=True)
class AddRelationshipCommand(Command):
    scene_id: str
    relationship: SpatialRelationship


@dataclass(frozen=True, kw_only=True)
class ImportDicomSeriesCommand(Command):
    """Import a DICOM series from a folder into the Scene.

    The handler uses `DicomSeriesReader` (from
    `infrastructure/imaging/dicom/`) to load, validate, sort,
    calibrate, and assemble the series into a `Volume`.

    The `object_id` is the stable identifier under which the Volume
    is registered in the `DomainObjectStore`. The caller is
    responsible for generating a unique ID.
    """

    scene_id: str
    path: str
    object_id: str

    def __post_init__(self) -> None:
        if not self.scene_id:
            raise ValueError("scene_id must not be empty")
        if not self.path:
            raise ValueError("path must not be empty")
        if not self.object_id:
            raise ValueError("object_id must not be empty")
