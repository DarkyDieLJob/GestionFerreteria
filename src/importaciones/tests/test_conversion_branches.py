import os
import types
import pytest

import importaciones.services.conversion as conv


class DummyIloc:
    def __getitem__(self, key):
        # Simula fallo del camino normal df.iloc[sr:]
        raise Exception("getitem not supported in this mock")

    def __call__(self, *args, **kwargs):
        # Camino alternativo: tratar iloc como callable
        return DummyDF(callable_used=True)


class DummyDF:
    def __init__(self, callable_used=False, fail_to_csv=False, has_reset=True):
        self.callable_used = callable_used
        self.fail_to_csv = fail_to_csv
        self.has_reset = has_reset
        self.iloc = DummyIloc()

    def reset_index(self, drop=False):
        if not self.has_reset:
            raise Exception("no reset_index in this mock")
        return self

    def to_csv(self, path, index=False, header=False, encoding="utf-8", sep=",", decimal="."):
        if self.fail_to_csv:
            raise Exception("write error")
        # escribir algo mínimo
        with open(path, "w", encoding=encoding) as f:
            f.write("a\n")


class DummyExcel:
    def __init__(self, sheet_names, fail_parse=False, df=None):
        self.sheet_names = sheet_names
        self._fail_parse = fail_parse
        self._df = df or DummyDF()

    def parse(self, name, header=None):
        if self._fail_parse:
            raise Exception("parse error")
        return self._df


class DummyPD(types.SimpleNamespace):
    def __init__(self, excel_obj):
        super().__init__()
        self._excel_obj = excel_obj

    def ExcelFile(self, input_path, engine=None):  # noqa: N802 (pandas name)
        return self._excel_obj


@pytest.mark.parametrize(
    "ext,engine",
    [
        (".xlsx", "openpyxl"),
        (".xls", "xlrd"),
        (".ods", "odf"),
    ],
)
def test_engine_selection_and_basic_flow(tmp_path, monkeypatch, ext, engine):
    input_path = tmp_path / f"test{ext}"
    input_path.write_text("dummy", encoding="utf-8")

    excel = DummyExcel(sheet_names=["Hoja1"], df=DummyDF())
    monkeypatch.setattr(conv, "_get_pandas", lambda: DummyPD(excel))

    out = conv.convertir_a_csv(str(input_path), output_dir=None, sheet_name=0, start_row=0)
    # Debe crear test.csv en el directorio del archivo (al usar output_dir=None)
    expected = os.path.join(os.path.dirname(str(input_path)), "test.csv")
    assert out == expected
    assert os.path.exists(out)


def test_unsupported_extension_raises():
    with pytest.raises(ValueError):
        conv.convertir_a_csv("/tmp/file.txt")


def test_missing_pandas_raises_runtime(monkeypatch):
    def _boom():
        raise ImportError("no pandas")
    monkeypatch.setattr(conv, "_get_pandas", _boom)
    with pytest.raises(RuntimeError) as e:
        conv.convertir_a_csv("/tmp/file.xlsx")
    assert "pandas es requerido" in str(e.value)


def test_excel_open_failure(monkeypatch):
    class PD(types.SimpleNamespace):
        def ExcelFile(self, input_path, engine=None):
            raise Exception("cannot open")
    monkeypatch.setattr(conv, "_get_pandas", lambda: PD())
    with pytest.raises(RuntimeError) as e:
        conv.convertir_a_csv("/tmp/file.xlsx")
    assert "No se pudo abrir el archivo" in str(e.value)


def test_sheet_index_out_of_range(monkeypatch, tmp_path):
    excel = DummyExcel(sheet_names=["Hoja1"])
    monkeypatch.setattr(conv, "_get_pandas", lambda: DummyPD(excel))
    with pytest.raises(ValueError):
        conv.convertir_a_csv(str(tmp_path / "file.xlsx"), sheet_name=5)


def test_sheet_name_missing(monkeypatch, tmp_path):
    excel = DummyExcel(sheet_names=["H1", "H2"])
    monkeypatch.setattr(conv, "_get_pandas", lambda: DummyPD(excel))
    with pytest.raises(ValueError):
        conv.convertir_a_csv(str(tmp_path / "file.xlsx"), sheet_name="NoExiste")


def test_parse_failure_raises(monkeypatch, tmp_path):
    excel = DummyExcel(sheet_names=["Hoja1"], fail_parse=True)
    monkeypatch.setattr(conv, "_get_pandas", lambda: DummyPD(excel))
    with pytest.raises(RuntimeError):
        conv.convertir_a_csv(str(tmp_path / "file.xlsx"), sheet_name=0)


def test_iloc_callable_and_reset_index_missing(monkeypatch, tmp_path):
    # DF sin reset_index para cubrir el except de reset_index
    df = DummyDF(callable_used=False, has_reset=False)
    excel = DummyExcel(sheet_names=["Hoja1"], df=df)
    monkeypatch.setattr(conv, "_get_pandas", lambda: DummyPD(excel))

    out = conv.convertir_a_csv(str(tmp_path / "file.xlsx"), sheet_name=0, start_row=2)
    assert os.path.exists(out)


def test_to_csv_failure_raises(monkeypatch, tmp_path):
    df = DummyDF(fail_to_csv=True)
    excel = DummyExcel(sheet_names=["Hoja1"], df=df)
    monkeypatch.setattr(conv, "_get_pandas", lambda: DummyPD(excel))
    with pytest.raises(RuntimeError):
        conv.convertir_a_csv(str(tmp_path / "file.xlsx"), sheet_name=0)
