from django.db import IntegrityError
from django.test import TestCase

from proveedores.adapters.models import Proveedor
from importaciones.adapters.models import ConfigImportacion


class ImportacionesModelsTest(TestCase):
    databases = {'default', 'negocio_db'}

    def setUp(self):
        self.prov = Proveedor.objects.create(nombre="Proveedor I", abreviatura="pi")

    def test_config_importacion_unique_por_proveedor(self):
        ConfigImportacion.objects.create(proveedor=self.prov, col_codigo="A")
        with self.assertRaises(IntegrityError):
            ConfigImportacion.objects.create(proveedor=self.prov, col_codigo="B")

    def test_config_importacion_campos_opcionales(self):
        cfg = ConfigImportacion.objects.create(proveedor=self.prov)
        self.assertIsNone(cfg.col_codigo)
# Pruebas para los adaptadores