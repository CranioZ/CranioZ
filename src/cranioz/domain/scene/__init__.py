"""Scene domain — spatial organization of objects.

Public API:
- Scene — spatial organization within a planning context.
- DomainObjectStore — canonical registry of domain objects.
- Transform — rigid transformation.
- SpatialRelationship — typed link between objects.
"""

from cranioz.domain.scene.domain_object_store import (
    DomainObjectStore,
    DomainObjectStoreError,
    ObjectAlreadyExists,
    ObjectInUse,
    ObjectNotFound,
)
from cranioz.domain.scene.relationship import SpatialRelationship
from cranioz.domain.scene.scene import (
    HierarchyCycle,
    ObjectAlreadyInScene,
    ObjectNotInScene,
    Scene,
    SceneError,
)
from cranioz.domain.scene.transform import Quaternion, Transform, Vector3

__all__ = [
    "DomainObjectStore",
    "DomainObjectStoreError",
    "HierarchyCycle",
    "ObjectAlreadyExists",
    "ObjectAlreadyInScene",
    "ObjectInUse",
    "ObjectNotFound",
    "ObjectNotInScene",
    "Quaternion",
    "Scene",
    "SceneError",
    "SpatialRelationship",
    "Transform",
    "Vector3",
]
