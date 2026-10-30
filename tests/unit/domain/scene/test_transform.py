"""Tests for Transform, Vector3, Quaternion."""

from cranioz.domain.scene.transform import Quaternion, Transform, Vector3


def test_identity_transform() -> None:
    t = Transform.identity()
    assert t.is_identity()
    assert t.translation == Vector3()
    assert t.rotation == Quaternion()


def test_non_identity_transform() -> None:
    t = Transform(translation=Vector3(1.0, 2.0, 3.0))
    assert not t.is_identity()
