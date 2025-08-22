from django.test import TestCase
from django.utils import timezone

from proveedores.adapters.models import Proveedor
from precios.adapters.models import Descuento, PrecioDeLista
from articulos.adapters.models import Articulo, ArticuloProveedor, ArticuloSinRevisar


class NegocioIntegrationTest(TestCase):
    databases = {"default"}

    def test_flujo_completo_precios_descuentos_articulos_proveedores(self):
        # 1) Proveedor
        prov = Proveedor.objects.create(nombre="Proveedor INT", abreviatura="pi")
        self.assertEqual(prov.abreviatura, "PI")
        # Con el router unificado, todo usa 'default'
        self.assertEqual(prov._state.db, "default")

        # 2) Descuento temporal general activo (10%)
        d = Descuento.objects.create(
            tipo="Promo INT",
            temporal=True,
            general=0.10,
            desde=timezone.now() - timezone.timedelta(days=1),
            hasta=timezone.now() + timezone.timedelta(days=1),
        )
        self.assertTrue(d.is_active())
        self.assertEqual(d._state.db, "default")

        # 3) Precio de lista con IVA y bulto
        pl = PrecioDeLista.objects.create(
            codigo="0005/",
            descripcion="Lista INT",
            precio=100,
            proveedor=prov,
            iva=0.21,
            bulto=5,
            stock=100,
        )
        self.assertEqual(pl.codigo, "5/")  # normalización de código
        self.assertEqual(pl._state.db, "default")

        # 4) Artículo y relación ArticuloProveedor
        art = Articulo.objects.create(codigo_barras="INT-ART-001")
        ap = ArticuloProveedor.objects.create(
            articulo=art,
            proveedor=prov,
            precio_de_lista=pl,
            codigo_proveedor="0005/",
            precio=100,
            stock=10,
            dividir=True,
            descuento=d,
        )
        self.assertEqual(ap.codigo_proveedor, "5/")
        self.assertEqual(ap.get_codigo_completo(), "5/".rstrip("/") + "/" + prov.abreviatura)

        # 5) Calcular precios end-to-end
        precios = art.generar_precios(cantidad=1, pago_efectivo=False)
        # Sin descuento general: base=(100/5)*(1+0.21)=24.2; final=36.3; final_efectivo=32.67; bulto=181.5
        # Con 10% OFF general activo: finales *0.9
        import math
        self.assertAlmostEqual(float(precios["base"]), 24.2, places=2)
        self.assertAlmostEqual(float(precios["final"]), 36.3 * 0.9, places=2)
        self.assertAlmostEqual(float(precios["final_efectivo"]), 32.67 * 0.9, places=1)
        self.assertAlmostEqual(float(precios["bulto"]), 181.5, places=2)
        self.assertAlmostEqual(float(precios["final_bulto"]), 181.5 * 0.9, places=2)
        self.assertAlmostEqual(float(precios["final_bulto_efectivo"]), (181.5 * 0.9) * 0.90, places=1)

    def test_bulto_aplicado_cuando_cantidad_supera_umbral(self):
        prov = Proveedor.objects.create(nombre="Prov BULTO", abreviatura="pb")
        d = Descuento.objects.create(
            tipo="SinGeneral",
            temporal=False,
            general=0.0,
        )
        pl = PrecioDeLista.objects.create(
            codigo="0007/",
            descripcion="Lista BULTO",
            precio=100,
            proveedor=prov,
            iva=0.21,
            bulto=5,
            stock=10,
        )
        art = Articulo.objects.create(codigo_barras="BUL-001")
        ArticuloProveedor.objects.create(
            articulo=art,
            proveedor=prov,
            precio_de_lista=pl,
            codigo_proveedor="0007/",
            precio=100,
            stock=10,
            dividir=True,
            descuento=d,
        )
        precios = art.generar_precios(cantidad=5, pago_efectivo=False)
        # base=(100/5)*1.21=24.2; final=36.3; bulto=36.3*5=181.5; con umbral, final_bulto = bulto * config.bulto(=0.05)
        self.assertAlmostEqual(float(precios["base"]), 24.2, places=2)
        self.assertAlmostEqual(float(precios["bulto"]), 181.5, places=2)
        self.assertAlmostEqual(float(precios["final_bulto"]), 181.5 * float(d.bulto), places=2)
        self.assertAlmostEqual(float(precios["final_bulto_efectivo"]), (181.5 * float(d.bulto)) * float(prov.margen_ganancia_efectivo), places=2)

    def test_pago_efectivo_flag_invariante_actualmente(self):
        prov = Proveedor.objects.create(nombre="Prov EF", abreviatura="pe")
        d = Descuento.objects.create(tipo="SinGen", temporal=False, general=0.0)
        pl = PrecioDeLista.objects.create(codigo="0011/", descripcion="Lista EF", precio=200, proveedor=prov, iva=0.21, bulto=1)
        art = Articulo.objects.create(codigo_barras="EF-001")
        ArticuloProveedor.objects.create(articulo=art, proveedor=prov, precio_de_lista=pl, codigo_proveedor="0011/", precio=200, stock=3, dividir=False, descuento=d)
        p_false = art.generar_precios(cantidad=1, pago_efectivo=False)
        p_true = art.generar_precios(cantidad=1, pago_efectivo=True)
        # Dado que el flag no se usa en la implementación actual, ambos resultados deben coincidir
        self.assertEqual(p_false, p_true)

    def test_bulto_y_pago_efectivo_en_umbral(self):
        prov = Proveedor.objects.create(nombre="Prov MIX", abreviatura="pm")
        d = Descuento.objects.create(tipo="SinGen", temporal=False, general=0.0)
        pl = PrecioDeLista.objects.create(codigo="0021/", descripcion="Lista MIX", precio=120, proveedor=prov, iva=0.21, bulto=4)
        art = Articulo.objects.create(codigo_barras="MIX-001")
        ArticuloProveedor.objects.create(articulo=art, proveedor=prov, precio_de_lista=pl, codigo_proveedor="0021/", precio=120, stock=10, dividir=True, descuento=d)
        precios_no_ef = art.generar_precios(cantidad=4, pago_efectivo=False)
        precios_ef = art.generar_precios(cantidad=4, pago_efectivo=True)
        # Implementación actual no usa pago_efectivo para alterar el cálculo -> iguales
        self.assertEqual(precios_no_ef, precios_ef)
        # Validar que al estar en umbral se usa rama de bulto con multiplicador de descuento.bulto
        self.assertIn("final_bulto", precios_ef)

    def test_mismo_codigo_pero_distinto_proveedor_permitido(self):
        a = Proveedor.objects.create(nombre="Prov A", abreviatura="pa")
        b = Proveedor.objects.create(nombre="Prov B", abreviatura="pb")
        PrecioDeLista.objects.create(codigo="0003/", descripcion="L1", precio=10, proveedor=a)
        # Debe permitirse el mismo codigo con otro proveedor por unique_together
        PrecioDeLista.objects.create(codigo="0003/", descripcion="L2", precio=20, proveedor=b)
        self.assertEqual(PrecioDeLista.objects.filter(codigo="3/").count(), 2)

    def test_superposicion_de_descuentos_solo_aplica_el_asignado(self):
        prov = Proveedor.objects.create(nombre="Prov D", abreviatura="pd")
        pl = PrecioDeLista.objects.create(codigo="0031/", descripcion="LD", precio=200, proveedor=prov, iva=0.21, bulto=1)
        from django.utils import timezone
        d10 = Descuento.objects.create(tipo="G10", temporal=True, general=0.10, desde=timezone.now()-timezone.timedelta(days=1), hasta=timezone.now()+timezone.timedelta(days=1))
        d15 = Descuento.objects.create(tipo="G15", temporal=True, general=0.15, desde=timezone.now()-timezone.timedelta(days=1), hasta=timezone.now()+timezone.timedelta(days=1))
        art = Articulo.objects.create(codigo_barras="D-001")
        # Asignamos SOLO d15 al ArticuloProveedor
        ArticuloProveedor.objects.create(articulo=art, proveedor=prov, precio_de_lista=pl, codigo_proveedor="0031/", precio=200, stock=5, dividir=False, descuento=d15)
        precios = art.generar_precios(cantidad=1, pago_efectivo=False)
        # Sin descuentos: base=200*1.21=242; final=242*1.5=363
        # Aplica SOLO 15% una vez: 363*0.85 = 308.55
        self.assertAlmostEqual(float(precios["final"]), round(363*0.85, 2), places=2)
        # Asegurar que no se compone 10% y 15% (que daría 308.55*0.9 indebido)
        self.assertNotAlmostEqual(float(precios["final"]), round(363*0.85*0.9, 2), places=2)

    def test_is_active_bordes_temporales_inclusivos(self):
        from django.utils import timezone
        prov = Proveedor.objects.create(nombre="Prov T", abreviatura="pt")
        pl = PrecioDeLista.objects.create(codigo="0041/", descripcion="LT", precio=100, proveedor=prov)
        art = Articulo.objects.create(codigo_barras="T-001")
        now = timezone.now()
        d = Descuento.objects.create(tipo="EDGE", temporal=True, general=0.10, desde=now, hasta=now)
        # Asignado el descuento en el borde exacto
        ArticuloProveedor.objects.create(articulo=art, proveedor=prov, precio_de_lista=pl, codigo_proveedor="0041/", precio=100, stock=1, dividir=False, descuento=d)
        precios = art.generar_precios(cantidad=1, pago_efectivo=False)
        # Con IVA por defecto 0.21: base=121; final=181.5; con 10% OFF => 163.35
        self.assertAlmostEqual(float(precios["final"]), 163.35, places=2)

    def test_performance_generar_precios_dividir_false_y_bulto_mayor_uno(self):
        from django.test.utils import CaptureQueriesContext
        from django.db import connections
        prov = Proveedor.objects.create(nombre="Prov P1", abreviatura="p1")
        d = Descuento.objects.create(tipo="SinGen", temporal=False, general=0.0)
        pl = PrecioDeLista.objects.create(codigo="0051/", descripcion="LP1", precio=80, proveedor=prov, iva=0.21, bulto=3)
        art = Articulo.objects.create(codigo_barras="P1-001")
        ArticuloProveedor.objects.create(articulo=art, proveedor=prov, precio_de_lista=pl, codigo_proveedor="0051/", precio=80, stock=9, dividir=False, descuento=d)
        with self.assertNumQueries(8, using="default"):
            art.generar_precios(cantidad=1, pago_efectivo=False)

    def test_performance_generar_precios_articulo_sin_revisar(self):
        prov = Proveedor.objects.create(nombre="Prov ASR P", abreviatura="pp")
        # Asegurar que exista el descuento por defecto
        Descuento.objects.get_or_create(tipo="Sin Descuento", defaults={"temporal": False, "general": 0.0})
        asr = ArticuloSinRevisar.objects.create(proveedor=prov, codigo_proveedor="0061/", descripcion_proveedor="X", nombre="ASR-P", precio=60, stock=1, descripcion="d")
        with self.assertNumQueries(2, using="default"):
            asr.generar_precios(cantidad=1, pago_efectivo=False)

    def test_articulo_sin_revisar_end_to_end(self):
        prov = Proveedor.objects.create(nombre="Prov SR", abreviatura="ps")
        # Asegurar que exista el descuento por defecto esperado por save()
        Descuento.objects.get_or_create(tipo="Sin Descuento", defaults={
            "temporal": False,
            "general": 0.0,
        })
        asr = ArticuloSinRevisar.objects.create(
            proveedor=prov,
            codigo_proveedor="0009/",
            descripcion_proveedor="Item SR",
            nombre="ASR",
            precio=50,
            stock=2,
            descripcion="desc",
        )
        # Normaliza código y asigna descuento "Sin Descuento" si no está definido
        self.assertEqual(asr.codigo_proveedor, "9/")
        precios = asr.generar_precios(cantidad=1, pago_efectivo=False)
        # iva=0 y bulto=1 para ASR, sin descuento general: base=50; final=75; final_efectivo=75*0.9=67.5
        self.assertAlmostEqual(float(precios["base"]), 50.0, places=2)
        self.assertAlmostEqual(float(precios["final"]), 75.0, places=2)
        self.assertAlmostEqual(float(precios["final_efectivo"]), 67.5, places=2)
