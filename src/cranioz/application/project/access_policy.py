"""ProjectAccessPolicy — authorization contract for project lifecycle.

The policy answers "may this actor perform this operation on this
project?". It is evaluated at the Project Manager boundary
(project.md §15): the Manager consults the policy before mutating
state, never after.

Design rules (see `project.md` §15, §28):

- The policy is a Protocol. Concrete implementations may be
  permissive (single-user, development, first boot) or restrictive
  (institutional deployments, role-based access).
- The policy is **read-only**. It does not mutate state, does not
  publish events, does not access persistence. It receives an
  `Actor` and a `ProjectId` (or nothing, for `can_create`) and
  returns a boolean.
- An `Actor` is a string for now. It identifies who is performing
  the operation. In single-user mode (the initial deployment), the
  bootstrap passes a stable identifier (e.g. the OS username, or a
  configured professional id). When the application gains a proper
  user model, `Actor` will become a richer value object; the
  Protocol signature will not need to change for the common case.
- `AllowAllProjectAccessPolicy` is the initial implementation. It
  returns True for every operation. It exists so the Project
  Manager has a policy to consult from day one, and so tests can
  substitute a denying policy to verify the Manager's error paths.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cranioz.domain.project.project_id import ProjectId

# An Actor identifies who is performing the operation. Kept as a
# string alias for now; the application has no user model yet.
# When a proper user model exists (roles, institutions), this alias
# becomes a class, and callers that already pass strings continue
# to work via a compatibility shim.
Actor = str


@runtime_checkable
class ProjectAccessPolicy(Protocol):
    """Authorization contract for project lifecycle operations."""

    def can_create(self, actor: Actor) -> bool:
        """Return True if `actor` may create a new project."""
        ...

    def can_open(self, actor: Actor, project_id: ProjectId) -> bool:
        """Return True if `actor` may open the given project."""
        ...

    def can_update(self, actor: Actor, project_id: ProjectId) -> bool:
        """Return True if `actor` may update the given project."""
        ...

    def can_delete(self, actor: Actor, project_id: ProjectId) -> bool:
        """Return True if `actor` may delete the given project."""
        ...


class AllowAllProjectAccessPolicy:
    """Permissive policy: every actor may do everything.

    This is the initial implementation for single-user deployments
    and for tests that do not care about authorization. It is a
    deliberate no-op, not a security boundary. A future
    RoleBasedProjectAccessPolicy will replace it for institutional
    deployments without changing the Project Manager's code.
    """

    def can_create(self, actor: Actor) -> bool:
        return True

    def can_open(self, actor: Actor, project_id: ProjectId) -> bool:
        return True

    def can_update(self, actor: Actor, project_id: ProjectId) -> bool:
        return True

    def can_delete(self, actor: Actor, project_id: ProjectId) -> bool:
        return True
