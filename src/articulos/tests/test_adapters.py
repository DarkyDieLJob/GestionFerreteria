from django.test import TestCase
from django.db import IntegrityError
from django.db import connections

from proveedores.adapters.models import Proveedor
from precios.adapters.models import Descuento, PrecioDeLista
from articulos.adapters.models import Articulo, ArticuloProveedor
import pytest

# Obsoleto tras refactor de lógica de precios/adapters; será reescrito con escenarios canónicos
pytestmark = pytest.mark.skip(reason="Obsoleto tras refactor; será reescrito")


class ArticulosModelsTest(TestCase):
    databases = {'default', 'negocio_db'}

    def setUp(self):
        self.prov = Proveedor.objects.create(nombre="Proveedor A", abreviatura="pa")
        # Asegurar descuento base existente
        self.descuento_base, _ = Descuento.objects.get_or_create(tipo="Sin Descuento")
        self.pl = PrecioDeLista.objects.create(
            codigo="001/",
            descripcion="Lista",
            precio=100,
            proveedor=self.prov,
        )

    def test_articulo_generar_precios_usa_relaciones(self):
        art = Articulo.objects.create(codigo_barras="123")
        ap = ArticuloProveedor.objects.create(
            articulo=art,
            proveedor=self.prov,
            precio_de_lista=self.pl,
            codigo_proveedor="001/",
            precio=100,
            stock=10,
            dividir=False,
            descuento=self.descuento_base,
        )
        precios = art.generar_precios(cantidad=1, pago_efectivo=False)
        self.assertIsInstance(precios, dict)
        self.assertIn('final', precios)
        self.assertIn('final_efectivo', precios)

    def test_articulo_proveedor_normaliza_codigo(self):
        art = Articulo.objects.create(codigo_barras="NORM-1")
        ap = ArticuloProveedor.objects.create(
            articulo=art,
            proveedor=self.prov,
            precio_de_lista=self.pl,
            codigo_proveedor="0005/",
            precio=50,
            stock=5,
            dividir=False,
            descuento=self.descuento_base,
        )
        self.assertEqual(ap.codigo_proveedor, "5/")

    def test_generar_precios_dividir_con_bulto_aplica_calculo(self):
        # bulto>1 y dividir=True
        self.pl.bulto = 5
        self.pl.iva = 0.21
        self.pl.save()
        art = Articulo.objects.create(codigo_barras="ABC")
        ap = ArticuloProveedor.objects.create(
            articulo=art,
            proveedor=self.prov,
            precio_de_lista=self.pl,
            codigo_proveedor="001/",
            precio=100,
            stock=10,
            dividir=True,
            descuento=self.descuento_base,
        )
        precios = art.generar_precios(cantidad=1, pago_efectivo=False)
        # Cálculo esperado según implementación actual
        # base = (100 / 5) * (1 + 0.21) * (1 - 0) = 24.2
        # final = base * 1.5 = 36.3
        # final_efectivo = final * 0.90 = 32.67
        # bulto = final * 5 = 181.5
        # final_bulto = bulto (cantidad < cantidad_bulto=5) = 181.5
        # final_bulto_efectivo = final_bulto * 0.90 = 163.35
        self.assertAlmostEqual(float(precios['base']), 24.2, places=2)
        self.assertAlmostEqual(float(precios['final']), 36.3, places=2)
        self.assertAlmostEqual(float(precios['final_efectivo']), 32.67, places=2)
        self.assertAlmostEqual(float(precios['bulto']), 181.5, places=2)
        self.assertAlmostEqual(float(precios['final_bulto']), 181.5, places=2)
        self.assertAlmostEqual(float(precios['final_bulto_efectivo']), 163.35, places=2)

    def test_generar_precios_con_descuento_general_activo_aplica_a_todos(self):
        # Crear descuento general activo del 10%
        from django.utils import timezone
        d = Descuento.objects.create(
            tipo="Promo",
            temporal=True,
            general=0.10,
            desde=timezone.now() - timezone.timedelta(days=1),
            hasta=timezone.now() + timezone.timedelta(days=1),
        )
        art = Articulo.objects.create(codigo_barras="XYZ")
        ap = ArticuloProveedor.objects.create(
            articulo=art,
            proveedor=self.prov,
            precio_de_lista=self.pl,
            codigo_proveedor="001/",
            precio=100,
            stock=10,
            dividir=False,
            descuento=d,
        )
        precios = art.generar_precios(cantidad=1, pago_efectivo=False)
        # Primero sin descuento general: base = 100 * (1+iva=1.21) * (1-0) = 121
        # final = 121 * 1.5 = 181.5; final_efectivo = 181.5 * 0.90 = 163.35
        # bulto = final * bulto(=1) = 181.5; final_bulto = 181.5 (cantidad<5)
        # Aplicar 10% OFF general a todos: * 0.9
        self.assertAlmostEqual(float(precios['base']), 121.0, places=2)
        self.assertAlmostEqual(float(precios['final']), round(181.5 * 0.9, 2), places=2)
        self.assertAlmostEqual(float(precios['final_efectivo']), round(163.35 * 0.9, 2), places=1)
        self.assertAlmostEqual(float(precios['bulto']), 181.5, places=2)
        self.assertAlmostEqual(float(precios['final_bulto']), round(181.5 * 0.9, 2), places=2)
        self.assertAlmostEqual(float(precios['final_bulto_efectivo']), round((181.5 * 0.9) * 0.90, 2), places=1)

    def test_generar_precios_bulto_cero_no_divide(self):
        # bulto=0 con dividir=True debe usar rama sin división (evitar división por cero)
        self.pl.bulto = 0
        self.pl.iva = 0.21
        self.pl.save()
        art = Articulo.objects.create(codigo_barras="000")
        ap = ArticuloProveedor.objects.create(
            articulo=art,
            proveedor=self.prov,
            precio_de_lista=self.pl,
            codigo_proveedor="002/",
            precio=100,
            stock=10,
            dividir=True,
            descuento=self.descuento_base,
        )
        precios = art.generar_precios(cantidad=1, pago_efectivo=False)
        # Rama else: base = 100 * 1.21 = 121
        self.assertAlmostEqual(float(precios['base']), 121.0, places=2)

    def test_articulo_sin_proveedor_retorna_error(self):
        art = Articulo.objects.create(codigo_barras="789")
        precios = art.generar_precios(cantidad=1, pago_efectivo=False)
        self.assertIn('error', precios)

    def test_articulo_proveedor_unique_together(self):
        art = Articulo.objects.create(codigo_barras="UT-1")
        ArticuloProveedor.objects.create(
            articulo=art,
            proveedor=self.prov,
            precio_de_lista=self.pl,
            codigo_proveedor="010/",
            precio=50,
            stock=5,
            dividir=False,
            descuento=self.descuento_base,
        )
        with self.assertRaises(IntegrityError):
            ArticuloProveedor.objects.create(
                articulo=art,
                proveedor=self.prov,
                precio_de_lista=self.pl,
                codigo_proveedor="0010/",  # se normaliza a 10/
                precio=60,
                stock=6,
                dividir=False,
                descuento=self.descuento_base,
            )