from django.test import TestCase
from django.utils import timezone

from proveedores.adapters.models import Proveedor
from precios.adapters.models import Descuento, PrecioDeLista


class PreciosModelsTest(TestCase):
    databases = {'default'}

    def setUp(self):
        self.prov = Proveedor.objects.create(nombre="Proveedor P", abreviatura="pp")

    def test_descuento_is_active_permanent(self):
        d = Descuento.objects.create(tipo="Sin Descuento")
        self.assertTrue(d.is_active())

    def test_descuento_is_active_temporal_in_range(self):
        now = timezone.now()
        d = Descuento.objects.create(
            tipo="Promo",
            temporal=True,
            desde=now - timezone.timedelta(days=1),
            hasta=now + timezone.timedelta(days=1),
        )
        self.assertTrue(d.is_active())

    def test_descuento_temporal_requires_dates(self):
        d = Descuento(tipo="Tmp", temporal=True)
        with self.assertRaises(ValueError):
            d.save()

    def test_precio_de_lista_normaliza_codigo_y_codigo_completo(self):
        pl = PrecioDeLista.objects.create(
            codigo="0037/",
            descripcion="Desc",
            precio=100,
            proveedor=self.prov,
        )
        self.assertEqual(pl.codigo, "37/")
        self.assertEqual(pl.get_codigo_completo(), "37/PP")

    def test_descuento_temporal_boundary_dates_are_active(self):
        now = timezone.now()
        d1 = Descuento.objects.create(tipo="B", temporal=True, desde=now, hasta=now)
        self.assertTrue(d1.is_active())

    def test_descuento_temporal_hasta_menor_que_desde_raises(self):
        now = timezone.now()
        with self.assertRaises(ValueError):
            Descuento.objects.create(tipo="Bad", temporal=True, desde=now, hasta=now - timezone.timedelta(minutes=1))

    def test_precio_de_lista_unique_por_proveedor_y_codigo(self):
        PrecioDeLista.objects.create(
            codigo="001/",
            descripcion="L1",
            precio=10,
            proveedor=self.prov,
        )
        with self.assertRaises(Exception):
            # Unique together should fail even if codigo se normaliza igual
            PrecioDeLista.objects.create(
                codigo="0001/",
                descripcion="L2",
                precio=20,
                proveedor=self.prov,
            )

    def test_precio_de_lista_defaults_iva_y_bulto(self):
        pl = PrecioDeLista.objects.create(
            codigo="9/",
            descripcion="Defaults",
            precio=50,
            proveedor=self.prov,
        )
        # Decimal comparison via str to avoid context issues
        self.assertEqual(str(pl.iva), str(0.21))
        self.assertEqual(str(pl.bulto), str(1))
# Pruebas para los adaptadores