import os
import tempfile

import pytest
from django.test import TestCase

from proveedores.adapters.models import Proveedor
from precios.adapters.models import Descuento
from importaciones.services.conversion import convertir_a_csv
from importaciones.services.importador_csv import importar_csv


BANNERS = [f"B{i}" for i in range(1, 15)]


def _write_layout1_dataframe(pd, path, engine):
    # Layout1: A=codigo, B=descripcion, C=precio
    data = [[b] for b in BANNERS]  # banners en col A solamente
    rows = [
        ["00012/", "Tornillo 12", "100.50"],
        ["", "Descripcion sin codigo", "200.00"],
        ["0000/", "Item ceros", "0"],
        ["00100/", "Tuerca", "not_a_number"],
    ]
    # Normalizar ancho a 3 columnas
    data = [r + [""] * (3 - len(r)) for r in data]
    df = pd.DataFrame(data + rows)
    df.to_excel(path, header=False, index=False, engine=engine)


def _write_layout2_dataframe(pd, path, engine):
    # Layout2: B=codigo, C=descripcion, F=precio (6 columnas)
    data = [[b] for b in BANNERS]
    data = [r + [""] * (6 - len(r)) for r in data]
    rows = [
        ["A-col", "00021/", "Descripcion 21", "", "", "123.45"],
        ["A-col", "", "Descripcion sin codigo", "", "", "200.00"],
        ["A-col", "0000/", "Item ceros", "", "", "0"],
        ["A-col", "00111/", "Tuerca", "", "", "not_a_number"],
    ]
    df = pd.DataFrame(data + rows)
    df.to_excel(path, header=False, index=False, engine=engine)


def _write_layout3_dataframe(pd, path, engine):
    # Layout3: F=codigo, B=descripcion, C=precio (6 columnas)
    data = [[b] for b in BANNERS]
    data = [r + [""] * (6 - len(r)) for r in data]
    rows = [
        ["Acol", "Descripcion 31", "123.00", "Dcol", "Ecol", "00031/"],
        ["Acol", "Descripcion sin codigo", "200.00", "Dcol", "Ecol", ""],
        ["Acol", "Item ceros", "0", "Dcol", "Ecol", "0000/"],
        ["Acol", "Tuerca", "not_a_number", "Dcol", "Ecol", "00141/"],
    ]
    df = pd.DataFrame(data + rows)
    df.to_excel(path, header=False, index=False, engine=engine)


class ConversionRealFilesTest(TestCase):
    databases = {'default'}

    def setUp(self):
        self.prov = Proveedor.objects.create(nombre="ProvConv", abreviatura="pc")
        Descuento.objects.get_or_create(tipo="Sin Descuento")
        self.start_row = 15

    def _run_and_assert(self, csv_path, col_codigo_idx, col_descripcion_idx, col_precio_idx):
        stats = importar_csv(
            proveedor=self.prov,
            ruta_csv=csv_path,
            start_row=self.start_row,
            col_codigo_idx=col_codigo_idx,
            col_descripcion_idx=col_descripcion_idx,
            col_precio_idx=col_precio_idx,
            dry_run=False,
        )
        assert stats.filas_leidas == 4
        assert stats.filas_validas == 2
        assert stats.filas_descartadas == 2

    def test_xlsx_conversion_and_import(self):
        try:
            import pandas as pd
        except Exception:
            pytest.skip('pandas not installed')
        # openpyxl is required by pandas engine; if missing, skip
        try:
            import openpyxl  # noqa: F401
        except Exception:
            pytest.skip('openpyxl not installed')
        with tempfile.TemporaryDirectory() as tmp:
            # layout1
            xlsx1 = os.path.join(tmp, 'layout1.xlsx')
            _write_layout1_dataframe(pd, xlsx1, engine='openpyxl')
            csv1 = convertir_a_csv(xlsx1)
            self._run_and_assert(csv1, 0, 1, 2)
            # layout2
            xlsx2 = os.path.join(tmp, 'layout2.xlsx')
            _write_layout2_dataframe(pd, xlsx2, engine='openpyxl')
            csv2 = convertir_a_csv(xlsx2)
            self._run_and_assert(csv2, 1, 2, 5)
            # layout3
            xlsx3 = os.path.join(tmp, 'layout3.xlsx')
            _write_layout3_dataframe(pd, xlsx3, engine='openpyxl')
            csv3 = convertir_a_csv(xlsx3)
            self._run_and_assert(csv3, 5, 1, 2)

    def test_xls_conversion_and_import(self):
        try:
            import pandas as pd
        except Exception:
            pytest.skip('pandas not installed')
        try:
            import xlrd  # noqa: F401
        except Exception:
            pytest.skip('xlrd not installed')
        # Necesitamos xlwt para escribir .xls con pandas
        try:
            import xlwt  # noqa: F401
        except Exception:
            pytest.skip('xlwt not installed')
        with tempfile.TemporaryDirectory() as tmp:
            xls1 = os.path.join(tmp, 'layout1.xls')
            _write_layout1_dataframe(pd, xls1, engine='xlwt')
            csv1 = convertir_a_csv(xls1)
            self._run_and_assert(csv1, 0, 1, 2)
            xls2 = os.path.join(tmp, 'layout2.xls')
            _write_layout2_dataframe(pd, xls2, engine='xlwt')
            csv2 = convertir_a_csv(xls2)
            self._run_and_assert(csv2, 1, 2, 5)
            xls3 = os.path.join(tmp, 'layout3.xls')
            _write_layout3_dataframe(pd, xls3, engine='xlwt')
            csv3 = convertir_a_csv(xls3)
            self._run_and_assert(csv3, 5, 1, 2)

    def test_ods_conversion_and_import(self):
        try:
            import pandas as pd
        except Exception:
            pytest.skip('pandas not installed')
        try:
            import odf  # noqa: F401
        except Exception:
            pytest.skip('odfpy not installed')
        with tempfile.TemporaryDirectory() as tmp:
            ods1 = os.path.join(tmp, 'layout1.ods')
            _write_layout1_dataframe(pd, ods1, engine='odf')
            csv1 = convertir_a_csv(ods1)
            self._run_and_assert(csv1, 0, 1, 2)
            ods2 = os.path.join(tmp, 'layout2.ods')
            _write_layout2_dataframe(pd, ods2, engine='odf')
            csv2 = convertir_a_csv(ods2)
            self._run_and_assert(csv2, 1, 2, 5)
            ods3 = os.path.join(tmp, 'layout3.ods')
            _write_layout3_dataframe(pd, ods3, engine='odf')
            csv3 = convertir_a_csv(ods3)
            self._run_and_assert(csv3, 5, 1, 2)
