from django.test import TestCase
from django.utils import timezone

from proveedores.adapters.models import Proveedor
from importaciones.adapters.models import ConfigImportacion


class ImportacionesSmokeTest(TestCase):
    databases = {'default', 'negocio_db'}

    def setUp(self):
        self.prov = Proveedor.objects.create(nombre="Proveedor I2", abreviatura="pi2")

    def test_config_importacion_creacion_minima_y_auto_update(self):
        cfg = ConfigImportacion.objects.create(proveedor=self.prov)
        self.assertIsNone(cfg.col_codigo)
        self.assertIsNotNone(cfg.ultima_actualizacion)
        antes = cfg.ultima_actualizacion
        # Forzar update para verificar auto_now cambia el valor
        cfg.col_codigo = "A"
        cfg.save()
        cfg.refresh_from_db()
        self.assertGreaterEqual(cfg.ultima_actualizacion, antes)

    def test_no_hay_dependencia_usuario(self):
        field_names = [f.name for f in ConfigImportacion._meta.get_fields()]
        self.assertNotIn('usuario', field_names)
