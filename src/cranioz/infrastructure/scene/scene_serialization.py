"""Serialization of Scene to/from JSON-compatible dicts.

Pure functions. No I/O. The shape is versioned via schema_version.
"""

from __future__ import annotations

from typing import Any

from cranioz.domain.scene.relationship import SpatialRelationship
from cranioz.domain.scene.scene import Scene
from cranioz.domain.scene.transform import Quaternion, Transform, Vector3

CURRENT_SCHEMA_VERSION = 1


class SceneSerializationError(ValueError):
    """Raised when a dict cannot be interpreted as a Scene."""


def scene_to_dict(scene: Scene) -> dict[str, Any]:
    members: list[dict[str, Any]] = []
    for object_id in scene.list_objects():
        transform = scene.get_transform(object_id)
        members.append(
            {
                "object_id": object_id,
                "parent_id": scene.get_parent(object_id),
                "transform": {
                    "translation": {
                        "x": transform.translation.x,
                        "y": transform.translation.y,
                        "z": transform.translation.z,
                    },
                    "rotation": {
                        "w": transform.rotation.w,
                        "x": transform.rotation.x,
                        "y": transform.rotation.y,
                        "z": transform.rotation.z,
                    },
                },
            }
        )
    relationships = [
        {
            "relationship_type": r.relationship_type,
            "source_id": r.source_id,
            "target_id": r.target_id,
            "directed": r.directed,
            "data": dict(r.data),
        }
        for r in scene.list_relationships()
    ]
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "scene_id": scene.scene_id,
        "members": members,
        "relationships": relationships,
    }


def scene_from_dict(data: dict[str, Any]) -> Scene:
    if not isinstance(data, dict):
        raise SceneSerializationError(f"scene data must be a dict, got {type(data).__name__}")
    schema_version = data.get("schema_version")
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise SceneSerializationError(f"unsupported schema_version: {schema_version}")
    scene_id = data.get("scene_id")
    if not isinstance(scene_id, str) or not scene_id:
        raise SceneSerializationError("scene_id must be a non-empty string")
    scene = Scene(scene_id=scene_id)
    for m in data.get("members", []):
        object_id = m["object_id"]
        scene.add_object(object_id)
        parent_id = m.get("parent_id")
        if parent_id is not None:
            scene.set_parent(object_id, parent_id)
        t = m.get("transform", {})
        scene.set_transform(
            object_id,
            Transform(
                translation=Vector3(
                    x=float(t["translation"]["x"]),
                    y=float(t["translation"]["y"]),
                    z=float(t["translation"]["z"]),
                ),
                rotation=Quaternion(
                    w=float(t["rotation"]["w"]),
                    x=float(t["rotation"]["x"]),
                    y=float(t["rotation"]["y"]),
                    z=float(t["rotation"]["z"]),
                ),
            ),
        )
    for r in data.get("relationships", []):
        scene.add_relationship(
            SpatialRelationship(
                relationship_type=r["relationship_type"],
                source_id=r["source_id"],
                target_id=r["target_id"],
                directed=bool(r.get("directed", True)),
                data=dict(r.get("data", {})),
            )
        )
    return scene
