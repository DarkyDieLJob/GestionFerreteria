import types
from unittest.mock import MagicMock
import importlib

import core_app.adapters.repository as repo_mod
from core_app.adapters.repository import DjangoCore_appRepository
from core_app.adapters.models import Core_app


class DummyConn:
    def cursor(self):
        # Return self as a context manager
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def setup_repo_mocks(monkeypatch):
    # Patch connections used inside the repository module
    monkeypatch.setattr(repo_mod, "connections", {"core_app_db": DummyConn()})
    # Patch model manager .objects.using(...) to return a mock manager
    manager = MagicMock()
    manager.create = MagicMock()
    manager.all = MagicMock(
        return_value=[
            Core_app(name="n1"),
            Core_app(name="n2"),
        ]
    )
    monkeypatch.setattr(
        Core_app, "objects", MagicMock(using=MagicMock(return_value=manager))
    )
    return manager


def test_save_invokes_create_with_data(monkeypatch):
    manager = setup_repo_mocks(monkeypatch)
    repo = DjangoCore_appRepository()
    data = {"name": "item X"}

    repo.save(data)

    manager.create.assert_called_once_with(**data)


def test_get_all_returns_queryset_like(monkeypatch):
    manager = setup_repo_mocks(monkeypatch)
    repo = DjangoCore_appRepository()

    result = repo.get_all()

    manager.all.assert_called_once_with()
    assert isinstance(result, list)
    assert len(result) == 2
