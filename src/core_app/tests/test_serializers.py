from unittest.mock import MagicMock
import pytest

from core_app.adapters import serializers as serializers_mod
from core_app.adapters.serializers import Core_appSerializer


def patch_serializer_model_manager(monkeypatch):
    manager = MagicMock()
    manager.create = MagicMock()
    # Patch objects manager used by the model referenced in the serializer module
    monkeypatch.setattr(serializers_mod.Core_app, "objects", MagicMock(using=MagicMock(return_value=manager)))
    # Patch create on the existing _default_manager used by DRF when calling create()
    monkeypatch.setattr(serializers_mod.Core_app._default_manager, "create", MagicMock(return_value=MagicMock()))
    return manager


def test_serializer_validates_required_fields():
    serializer = Core_appSerializer(data={"name": "abc"})
    assert serializer.is_valid(), serializer.errors


def test_serializer_invalid_without_name():
    serializer = Core_appSerializer(data={})
    assert not serializer.is_valid()
    assert "name" in serializer.errors


def test_serializer_create_calls_model_create(monkeypatch):
    manager = patch_serializer_model_manager(monkeypatch)
    serializer = Core_appSerializer(data={"name": "abc"})
    assert serializer.is_valid(), serializer.errors

    instance = serializer.save()

    # DRF's ModelSerializer.create uses ModelClass._default_manager.create
    serializers_mod.Core_app._default_manager.create.assert_called_once()
