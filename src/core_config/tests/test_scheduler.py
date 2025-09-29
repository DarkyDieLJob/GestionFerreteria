import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.test import override_settings

import core_config.scheduler as scheduler


class _FakeQS:
    def __init__(self, providers):
        self._providers = providers

    def all(self):
        return self._providers


class _FakeManager:
    def __init__(self, providers):
        self._providers = providers

    def using(self, alias):
        assert alias == "negocio_db"
        return _FakeQS(self._providers)


def _fake_model(providers):
    class _M:
        objects = _FakeManager(providers)
    return _M


@override_settings()
def test_run_procesar_excel_calls_subprocess_when_file_exists(tmp_path, monkeypatch, settings):
    settings.BASE_DIR = tmp_path

    # Arrange: fake providers with ids 1 and 2
    providers = [SimpleNamespace(id=1), SimpleNamespace(id=2)]

    def fake_get_model(app_label, model_name):
        assert app_label == "proveedores"
        assert model_name == "Proveedor"
        return _fake_model(providers)

    monkeypatch.setattr(scheduler, "apps", SimpleNamespace(get_model=fake_get_model))

    # Create only the file for provider 2
    imports_dir = tmp_path / "data" / "imports"
    imports_dir.mkdir(parents=True)
    target_file = imports_dir / "excel_2.xlsx"
    target_file.write_bytes(b"dummy")

    calls = []

    def fake_run(cmd, check):
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(scheduler, "subprocess", SimpleNamespace(run=fake_run))

    # Act
    scheduler.run_procesar_excel()

    # Assert
    assert len(calls) == 1
    cmd = calls[0]
    assert cmd[0] == sys.executable
    assert cmd[1].endswith(str(Path("src") / "importaciones" / "procesar_excel_script.py"))
    assert cmd[2] == "2"
    assert cmd[3] == str(target_file)


@override_settings()
def test_run_procesar_excel_skips_when_no_files(tmp_path, monkeypatch, settings):
    settings.BASE_DIR = tmp_path

    providers = [SimpleNamespace(id=5)]

    def fake_get_model(app_label, model_name):
        return _fake_model(providers)

    monkeypatch.setattr(scheduler, "apps", SimpleNamespace(get_model=fake_get_model))
    # Ensure imports dir exists but without files
    (tmp_path / "data" / "imports").mkdir(parents=True)

    calls = []

    def fake_run(cmd, check):
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(scheduler, "subprocess", SimpleNamespace(run=fake_run))

    scheduler.run_procesar_excel()

    assert calls == []


def test_main_returns_when_schedule_missing(monkeypatch, capsys):
    # Force import schedule to raise ModuleNotFoundError inside main()
    class _Importer:
        def __call__(self, name, *args, **kwargs):
            if name == "schedule":
                raise ModuleNotFoundError
            return __import__(name, *args, **kwargs)

    # Monkeypatch builtins.__import__ just for the scope of this call
    import builtins

    orig_import = builtins.__import__
    builtins.__import__ = _Importer()
    try:
        scheduler.main()
    finally:
        builtins.__import__ = orig_import

    out = capsys.readouterr().out
    assert "'schedule' no está instalada" in out or "schedule" in out


def test_main_with_schedule_runs_once(monkeypatch, capsys):
    # Inject a fake 'schedule' module to exercise the happy path
    class Every:
        @property
        def day(self):
            return self

        def at(self, _time):
            return self

        def do(self, fn):
            # store scheduled function for assertion
            self._scheduled = fn
            return None

    calls = []
    fake_schedule = SimpleNamespace(
        every=lambda: Every(),
    )

    def run_pending():
        calls.append("run")
        # Break the infinite loop after first iteration
        raise KeyboardInterrupt

    fake_schedule.run_pending = run_pending

    # Make import schedule return our fake module
    monkeypatch.setitem(sys.modules, "schedule", fake_schedule)
    # Avoid real sleeping
    monkeypatch.setattr(scheduler, "time", SimpleNamespace(sleep=lambda s: None))

    with pytest.raises(KeyboardInterrupt):
        scheduler.main()

    # One pending run attempted
    assert calls == ["run"]
