"""Tests for ActorRegistry."""

from cranioz.infrastructure.rendering.actor_registry import ActorRegistry


def test_register_and_get() -> None:
    registry = ActorRegistry()
    actor = object()
    registry.register("o-1", actor)
    assert registry.get("o-1") is actor


def test_unregister() -> None:
    registry = ActorRegistry()
    registry.register("o-1", object())
    removed = registry.unregister("o-1")
    assert removed is not None
    assert not registry.contains("o-1")


def test_unregister_unknown_returns_none() -> None:
    registry = ActorRegistry()
    assert registry.unregister("unknown") is None


def test_clear() -> None:
    registry = ActorRegistry()
    registry.register("o-1", object())
    registry.register("o-2", object())
    registry.clear()
    assert len(registry) == 0
