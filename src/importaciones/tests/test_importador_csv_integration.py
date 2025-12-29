import os
from django.test import TestCase

from proveedores.adapters.models import Proveedor
from importaciones.services.importador_csv import importar_csv
from precios.adapters.models import PrecioDeLista
from articulos.adapters.models import ArticuloSinRevisar
from precios.adapters.models import Descuento


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


class ImportadorCSVIntegrationTest(TestCase):
    def setUp(self):
        self.prov = Proveedor.objects.create(nombre="Proveedor Import", abreviatura="pi")
        self.start_row = 15
        # Asegurar descuento base requerido por ArticuloSinRevisar.save()
        Descuento.objects.get_or_create(tipo="Sin Descuento")

    def _assert_stats_and_side_effects(self, stats):
        # En cada layout: 4 filas visibles a partir de start_row
        # 2 válidas (1 y 3), 2 descartadas (2 sin código, 4 precio inválido)
        self.assertEqual(stats.filas_leidas, 4)
        self.assertEqual(stats.filas_validas, 2)
        self.assertEqual(stats.filas_descartadas, 2)
        # En una DB limpia deberían crearse 2 precios
        self.assertEqual(stats.creadas, 2)
        self.assertEqual(stats.actualizadas, 0)
        # Deben existir también ArticuloSinRevisar para los códigos válidos
        self.assertGreaterEqual(ArticuloSinRevisar.objects.filter(proveedor=self.prov).count(), 2)

    def test_layout1_csv(self):
        path = os.path.join(FIXTURES_DIR, 'layout1.csv')
        stats = importar_csv(
            proveedor=self.prov,
            ruta_csv=path,
            start_row=self.start_row,
            col_codigo_idx=0,  # A=codigo
            col_descripcion_idx=1,  # B=descripcion
            col_precio_idx=2,  # C=precio
            dry_run=False,
        )
        self._assert_stats_and_side_effects(stats)
        # Verificamos existencia de PrecioDeLista normalizado para un código típico
        self.assertTrue(PrecioDeLista.objects.filter(proveedor=self.prov).exists())

    def test_layout2_csv(self):
        path = os.path.join(FIXTURES_DIR, 'layout2.csv')
        stats = importar_csv(
            proveedor=self.prov,
            ruta_csv=path,
            start_row=self.start_row,
            col_codigo_idx=1,  # B=codigo
            col_descripcion_idx=2,  # C=descripcion
            col_precio_idx=5,  # F=precio
            dry_run=False,
        )
        self._assert_stats_and_side_effects(stats)

    def test_layout3_csv(self):
        path = os.path.join(FIXTURES_DIR, 'layout3.csv')
        stats = importar_csv(
            proveedor=self.prov,
            ruta_csv=path,
            start_row=self.start_row,
            col_codigo_idx=5,  # F=codigo
            col_descripcion_idx=1,  # B=descripcion
            col_precio_idx=2,  # C=precio
            dry_run=False,
        )
        self._assert_stats_and_side_effects(stats)
