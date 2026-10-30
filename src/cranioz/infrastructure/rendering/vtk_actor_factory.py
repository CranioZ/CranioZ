"""VTKActorFactory — creates VTK actors from domain objects.

The factory is the only component that knows how to translate a
domain object (Mesh, Volume, etc.) into a VTK actor. It does NOT
own the actor; the caller (VTKSceneRenderer) does.

For the first version, the factory supports:
- Mesh (placeholder: creates a vtkActor with a red sphere).
- Volume (placeholder: not implemented).

The placeholders will be replaced by real implementations once the
domain objects (Mesh, Volume) are implemented.

VTK is an optional dependency. The import is deferred to
``create_mesh_actor`` so that the application can boot without VTK
installed; the error is raised only when an actor is actually
created.

See scene.md §26.
"""

from __future__ import annotations

from typing import Any


class VTKActorFactory:
    """Creates VTK actors from domain objects."""

    def create_mesh_actor(self, object_id: str) -> Any:
        """Create a VTK actor for a Mesh object.

        For the first version, this returns a placeholder actor
        (a red sphere). A future version will read the actual mesh
        geometry from the domain object.
        """
        try:
            import vtk  # noqa: PLC0415 - deferred import to allow boot without VTK
        except ImportError as exc:
            raise RuntimeError("VTK is not installed. Install it with 'pip install vtk'.") from exc
        sphere = vtk.vtkSphereSource()
        sphere.SetRadius(10.0)
        sphere.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # red placeholder
        return actor

    def create_volume_actor(self, object_id: str) -> Any:
        """Create a VTK actor for a Volume object.

        Not implemented in the first version.
        """
        raise NotImplementedError("Volume rendering is not implemented yet.")
