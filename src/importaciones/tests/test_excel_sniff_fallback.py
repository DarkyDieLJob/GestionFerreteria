import os
import tempfile
from types import SimpleNamespace
from typing import List

import pytest


class _FakeExcelFile:
    def __init__(self, path, engine=None):
        self.path = path
        self.engine = engine
        self.sheet_names = ["Hoja1", "Hoja2"]


@pytest.fixture()
def temp_file_factory():
    created: List[str] = []

    def _make(prefix: bytes):
        fd, p = tempfile.mkstemp(suffix=".xls")
        os.close(fd)
        with open(p, "wb") as f:
            f.write(prefix + b"dummy")
        created.append(p)
        return p

    try:
        yield _make
    finally:
        for p in created:
            try:
                os.remove(p)
            except Exception:
                pass


def test_listar_hojas_excel_xlsx_like_uses_openpyxl(monkeypatch, temp_file_factory):
    from importaciones.adapters.repository import ExcelRepository

    xlsx_like = temp_file_factory(b"PK")

    repo = ExcelRepository()
    # Mock storage.path to return our temp path
    monkeypatch.setattr(repo, "storage", SimpleNamespace(path=lambda name: xlsx_like))

    calls = []

    def _excel_file(path, engine=None):
        calls.append((path, engine))
        return _FakeExcelFile(path, engine)

    import pandas as pd

    monkeypatch.setattr(pd, "ExcelFile", _excel_file)

    hojas = repo.listar_hojas_excel("whatever.xlsx")
    assert hojas == ["Hoja1", "Hoja2"]
    assert any(engine == "openpyxl" for (_p, engine) in calls)


def test_listar_hojas_excel_xls_like_falls_back_to_conversion(monkeypatch, temp_file_factory):
    from importaciones.adapters.repository import ExcelRepository

    xls_like = temp_file_factory(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1")

    repo = ExcelRepository()
    monkeypatch.setattr(repo, "storage", SimpleNamespace(path=lambda name: xls_like))

    import pandas as pd

    def _excel_file_raise_on_xlrd(path, engine=None):
        if engine == "xlrd":
            raise Exception("xlrd failed")
        return _FakeExcelFile(path, engine)

    monkeypatch.setattr(pd, "ExcelFile", _excel_file_raise_on_xlrd)

    class _FakeXLS2XLSX:
        def __init__(self, in_path):
            self.in_path = in_path

        def to_xlsx(self, out_path):
            fd, tmp = tempfile.mkstemp(suffix=".xlsx")
            os.close(fd)
            try:
                os.remove(out_path)
            except Exception:
                pass
            with open(out_path, "wb") as f:
                f.write(b"PKconverted")

    import sys

    fake_mod = SimpleNamespace(XLS2XLSX=_FakeXLS2XLSX)
    sys.modules["xls2xlsx"] = fake_mod

    hojas = repo.listar_hojas_excel("file.xls")
    assert hojas == ["Hoja1", "Hoja2"]


def test_conversion_convertir_a_csv_sniff_and_fallback(monkeypatch, temp_file_factory):
    from importaciones.services import conversion as conv

    xls_like = temp_file_factory(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1")

    class _FakeExcelFileConv:
        def __init__(self, path, engine=None):
            self.sheet_names = ["Sheet1"]
            self.path = path
            self.engine = engine

        def parse(self, name, header=None):
            class _DF:
                def __init__(self):
                    self._data = [[1, 2, 3]]

                def iloc(self, *args, **kwargs):
                    return self

                def reset_index(self, drop=True):
                    return self

                def to_csv(self, out_path, index=False, header=False, encoding="utf-8", sep=",", decimal="."):
                    with open(out_path, "w", encoding=encoding) as f:
                        f.write("1,2,3\n")

            return _DF()

    import pandas as pd

    def _excel_file_path_engine(path, engine=None):
        if engine == "xlrd":
            raise Exception("xlrd failed")
        return _FakeExcelFileConv(path, engine)

    monkeypatch.setattr(pd, "ExcelFile", _excel_file_path_engine)

    class _FakeXLS2XLSX:
        def __init__(self, in_path):
            self.in_path = in_path

        def to_xlsx(self, out_path):
            with open(out_path, "wb") as f:
                f.write(b"PKconverted")

    import sys

    sys.modules["xls2xlsx"] = SimpleNamespace(XLS2XLSX=_FakeXLS2XLSX)

    out = conv.convertir_a_csv(xls_like)
    assert out.endswith(".csv")
    assert os.path.exists(out)
    with open(out, "r", encoding="utf-8") as f:
        content = f.read().strip()
    assert content == "1,2,3"
