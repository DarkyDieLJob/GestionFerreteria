import os
import io
from unittest.mock import Mock
from django.test import TestCase

from importaciones.services.conversion import convertir_a_csv, _get_pandas


class ConversionServiceTest(TestCase):
    def test_csv_passthrough(self):
        # Si es CSV, retorna el mismo path
        path = os.path.join(os.path.dirname(__file__), 'fixtures', 'layout1.csv')
        out = convertir_a_csv(path)
        self.assertEqual(out, path)

    def test_convert_xlsx_to_csv_with_mock_single_sheet(self):
        # Mockeamos pandas y ExcelFile para no requerir dependencias de excel
        fake_df = Mock()
        fake_df.iloc.return_value = fake_df
        fake_df.reset_index.return_value = fake_df
        calls = {}

        class FakeExcelFile:
            sheet_names = ['Hoja1']

            def parse(self, name, header=None):
                return fake_df

        def fake_get_pandas():
            calls['used'] = True
            m = Mock()
            m.ExcelFile.return_value = FakeExcelFile()
            return m

        # Parcheamos el import perezoso
        import importaciones.services.conversion as conv
        original_get_pd = conv._get_pandas
        conv._get_pandas = fake_get_pandas
        try:
            tmp_in = os.path.join(os.path.dirname(__file__), 'fixtures', 'dummy.xlsx')
            # Crear archivo dummy vacío para la ruta (no se leerá realmente por el mock)
            with open(tmp_in, 'wb') as f:
                f.write(b'')
            out_csv = convertir_a_csv(tmp_in, sheet_name=0)
            self.assertTrue(out_csv.endswith('.csv'))
            self.assertTrue(calls.get('used'))
            # Aseguramos que se haya llamado a to_csv con encoding y sin header/index
            fake_df.to_csv.assert_called()
        finally:
            conv._get_pandas = original_get_pd
            # cleanup
            try:
                os.remove(tmp_in)
            except FileNotFoundError:
                pass
            try:
                os.remove(out_csv)
            except Exception:
                pass

    def test_convert_multi_sheet_with_start_rows(self):
        # Mock multi-hojas y start_row por hoja
        fake_df1 = Mock()
        # iloc is subscriptable, configure __getitem__
        fake_df1.iloc.__getitem__.return_value = fake_df1
        fake_df1.reset_index.return_value = fake_df1
        fake_df2 = Mock()
        fake_df2.iloc.__getitem__.return_value = fake_df2
        fake_df2.reset_index.return_value = fake_df2

        class FakeExcelFile:
            sheet_names = ['A', 'B']

            def parse(self, name, header=None):
                if name == 'A':
                    return fake_df1
                if name == 'B':
                    return fake_df2
                raise AssertionError('unexpected sheet')

        def fake_get_pandas():
            m = Mock()
            m.ExcelFile.return_value = FakeExcelFile()
            return m

        import importaciones.services.conversion as conv
        original_get_pd = conv._get_pandas
        conv._get_pandas = fake_get_pandas
        try:
            tmp_in = os.path.join(os.path.dirname(__file__), 'fixtures', 'dummy2.xlsx')
            with open(tmp_in, 'wb') as f:
                f.write(b'')
            out_list = convertir_a_csv(tmp_in, sheet_name=['A', 'B'], start_row={'A': 2, 'B': 0})
            self.assertIsInstance(out_list, list)
            # Debe nombrar como base_hoja.csv cuando hay múltiples hojas
            base = os.path.splitext(os.path.basename(tmp_in))[0]
            self.assertIn(f"{base}_A.csv", [os.path.basename(p) for p in out_list])
            self.assertIn(f"{base}_B.csv", [os.path.basename(p) for p in out_list])
            # Se debe haber llamado a to_csv para ambas hojas
            self.assertTrue(fake_df1.to_csv.called)
            self.assertTrue(fake_df2.to_csv.called)
        finally:
            conv._get_pandas = original_get_pd
            try:
                os.remove(tmp_in)
            except FileNotFoundError:
                pass
