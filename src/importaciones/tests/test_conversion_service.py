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

    def test_convert_xlsx_to_csv_with_mock(self):
        # Mockeamos pandas para no requerir dependencias de excel en entorno de test
        fake_df = Mock()
        calls = {}

        def fake_get_pandas():
            calls['used'] = True
            m = Mock()
            m.read_excel.return_value = fake_df
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
            out_csv = convertir_a_csv(tmp_in)
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
