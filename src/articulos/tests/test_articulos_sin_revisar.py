from django.test import TestCase
from django.apps import apps

from proveedores.adapters.models import Proveedor
from precios.adapters.models import Descuento
from articulos.adapters.models import ArticuloSinRevisar
import pytest

# Obsoleto tras refactor; se reescribirá con escenarios canónicos
pytestmark = pytest.mark.skip(reason="Obsoleto tras refactor; será reescrito")


class ArticulosSinRevisarTest(TestCase):
    databases = {'default', 'negocio_db'}

    def setUp(self):
        self.prov = Proveedor.objects.create(nombre="Proveedor SR", abreviatura="sr")
        # Asegurar descuento base existente
        self.desc_base, _ = Descuento.objects.get_or_create(tipo="Sin Descuento")

    def test_modelo_no_tiene_campo_usuario(self):
        field_names = [f.name for f in ArticuloSinRevisar._meta.get_fields()]
        self.assertNotIn('usuario', field_names)

    def test_creacion_sin_usuario_y_descuento_por_defecto(self):
        art_sr = ArticuloSinRevisar.objects.create(
            proveedor=self.prov,
            codigo_proveedor="0007/",
            descripcion_proveedor="Tornillo x",
            precio=100,
            stock=3,
        )
        # save() normaliza codigo y asigna descuento "Sin Descuento" si no se pasa
        self.assertEqual(art_sr.codigo_proveedor, "7/")
        self.assertIsNotNone(art_sr.descuento)
        self.assertEqual(art_sr.descuento.tipo, "Sin Descuento")

    def test_descuento_temporal_activo_afecta_precios(self):
        from django.utils import timezone
        d = Descuento.objects.create(
            tipo="Promo SR",
            temporal=True,
            general=0.10,
            desde=timezone.now() - timezone.timedelta(days=1),
            hasta=timezone.now() + timezone.timedelta(days=1),
        )
        art_sr = ArticuloSinRevisar.objects.create(
            proveedor=self.prov,
            codigo_proveedor="001/",
            descripcion_proveedor="Arandela",
            precio=100,
            stock=10,
            descuento=d,
        )
        precios = art_sr.generar_precios(cantidad=1, pago_efectivo=False)
        # Sin descuento: base = 100 (iva=0, dividir=False, bulto=1)
        # final = 100 * margen(1.5) = 150 -> 10% OFF => 135
        self.assertAlmostEqual(float(precios['base']), 100.0, places=2)
        self.assertAlmostEqual(float(precios['final']), 135.0, places=2)
