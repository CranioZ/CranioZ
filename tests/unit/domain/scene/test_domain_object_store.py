"""Tests for DomainObjectStore."""

import pytest

from cranioz.domain.scene.domain_object_store import (
    DomainObjectStore,
    ObjectAlreadyExists,
    ObjectNotFound,
)


def test_add_and_get() -> None:
    store = DomainObjectStore()
    obj = object()
    store.add("o-1", obj)
    assert store.get("o-1") is obj


def test_add_duplicate_raises() -> None:
    store = DomainObjectStore()
    store.add("o-1", object())
    with pytest.raises(ObjectAlreadyExists):
        store.add("o-1", object())


def test_get_unknown_raises() -> None:
    store = DomainObjectStore()
    with pytest.raises(ObjectNotFound):
        store.get("unknown")


def test_remove() -> None:
    store = DomainObjectStore()
    store.add("o-1", object())
    store.remove("o-1")
    assert not store.contains("o-1")


def test_remove_unknown_raises() -> None:
    store = DomainObjectStore()
    with pytest.raises(ObjectNotFound):
        store.remove("unknown")
