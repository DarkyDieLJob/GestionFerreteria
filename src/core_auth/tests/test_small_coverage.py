import builtins
import importlib
import sys
from unittest import mock
import pytest
from django.core.exceptions import ValidationError


def test_apps_ready_handles_import_error(monkeypatch):
    # Patch __import__ to raise for core_auth.signals
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.endswith("core_auth.signals"):
            raise Exception("boom")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from importlib import import_module
    from core_auth.apps import Core_authConfig

    # Ensure a fresh import attempt of signals
    sys.modules.pop("core_auth.signals", None)
    # Instantiate AppConfig with required args and call ready; should not raise
    Core_authConfig("core_auth", import_module("core_auth")).ready()


def test_login_use_case_missing_credentials_raises_code_missing_credentials():
    # Build a dummy repository; it shouldn't be called
    class DummyRepo:
        def authenticate_user(self, *a, **k):
            return None

    from core_auth.domain.use_cases import LoginUserUseCase

    uc = LoginUserUseCase(DummyRepo())
    with pytest.raises(ValidationError) as ei:
        uc.execute(username_or_email="", password="")
    err = ei.value
    # Ensure code is set as expected
    assert getattr(err, "code", None) == "missing_credentials"
