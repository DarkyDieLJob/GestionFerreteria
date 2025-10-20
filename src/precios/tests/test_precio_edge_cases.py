from django.test import TestCase

from proveedores.adapters.models import Proveedor
from precios.adapters.models import PrecioDeLista


class PrecioDeListaEdgeCasesTest(TestCase):
    def setUp(self):
        self.prov = Proveedor.objects.create(nombre="Proveedor P", abreviatura="pp")

    def test_normaliza_codigo_removiendo_ceros_y_agregando_slash(self):
        p = PrecioDeLista.objects.create(codigo="00012/", descripcion="L", precio=10, proveedor=self.prov)
        self.assertEqual(p.codigo, "12/")
        self.assertEqual(p.get_codigo_completo(), "12/PP")

    def test_bulto_y_iva_valores_borde(self):
        # bulto=0 debe persistir 0 y no romper normalización del código
        p = PrecioDeLista.objects.create(codigo="0000/", descripcion="L0", precio=10, proveedor=self.prov, iva=0, bulto=0)
        # Caso especial: todo ceros se conserva como "0000/" según implementación actual
        self.assertEqual(p.codigo, "0000/")
        self.assertEqual(float(p.iva), 0.0)
        self.assertEqual(float(p.bulto), 0.0)
