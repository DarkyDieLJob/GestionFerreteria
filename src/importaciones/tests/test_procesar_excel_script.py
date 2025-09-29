import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

import importaciones.procesar_excel_script as script


def test_script_exits_when_file_missing(tmp_path, monkeypatch, capsys):
    # Arrange CLI args: proveedor_id=7, file path that does not exist
    argv = ["python", "7", str(tmp_path / "missing.xlsx")]
    monkeypatch.setattr(sys, "argv", argv)

    # Act
    with pytest.raises(SystemExit) as exc:
        script.main()

    # Assert
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "Archivo no encontrado" in out


def test_script_calls_repository_and_prints_result(tmp_path, monkeypatch, capsys):
    # Arrange existing file
    excel_file = tmp_path / "excel_99.xlsx"
    excel_file.write_bytes(b"dummy")

    # Fake ExcelRepository
    calls = {}

    class FakeRepo:
        def procesar_excel(self, proveedor_id, nombre_archivo):
            calls["proveedor_id"] = proveedor_id
            calls["nombre_archivo"] = nombre_archivo
            return {"ok": True, "count": 3}

    monkeypatch.setattr(script, "ExcelRepository", FakeRepo)

    argv = ["python", "99", str(excel_file)]
    monkeypatch.setattr(sys, "argv", argv)

    # Act
    script.main()

    # Assert
    assert calls == {"proveedor_id": 99, "nombre_archivo": str(excel_file)}
    out = capsys.readouterr().out
    assert "{'ok': True, 'count': 3}" in out
