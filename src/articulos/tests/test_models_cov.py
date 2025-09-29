import pytest
from django.apps import apps
from django.test import override_settings


# Helpers using the default DB (adapters/models.py uses using('default'))

def ensure_descuento(tipo="Sin Descuento", using="default", **kwargs):
    Descuento = apps.get_model('precios', 'Descuento')
    obj, _ = Descuento.objects.using(using).get_or_create(tipo=tipo, defaults=kwargs)
    return obj


def make_proveedor(using="default", **kwargs):
    Proveedor = apps.get_model('proveedores', 'Proveedor')
    idx = Proveedor.objects.using(using).count() + 1
    defaults = dict(
        nombre=f"Prov SA {idx}",
        abreviatura=f"PV{idx}",
        descuento_comercial=0,
        margen_ganancia=1,
        margen_ganancia_efectivo=1,
    )
    defaults.update(kwargs)
    return Proveedor.objects.using(using).create(**defaults)


def make_precio_de_lista(proveedor=None, using="default", **kwargs):
    PrecioDeLista = apps.get_model('precios', 'PrecioDeLista')
    prov = proveedor or make_proveedor(using=using)
    params = dict(
        proveedor_id=prov.id,
        codigo=kwargs.pop('codigo', '1/'),
        descripcion=kwargs.pop('descripcion', 'PL'),
        precio=kwargs.pop('precio', 100),
        iva=kwargs.pop('iva', 21),
        bulto=kwargs.pop('bulto', 1),
    )
    params.update(kwargs)
    return PrecioDeLista.objects.using(using).create(**params)


def make_asr(proveedor=None, using="default", **kwargs):
    ArticuloSinRevisar = apps.get_model('articulos', 'ArticuloSinRevisar')
    prov = proveedor or make_proveedor(using=using)
    params = dict(
        proveedor_id=prov.id,
        codigo_proveedor=kwargs.pop('codigo_proveedor', '0007/'),
        descripcion_proveedor=kwargs.pop('descripcion_proveedor', 'ASR'),
        precio=kwargs.pop('precio', 50),
        stock=kwargs.pop('stock', 1),
        estado=kwargs.pop('estado', 'pendiente'),
    )
    params.update(kwargs)
    return ArticuloSinRevisar.objects.using(using).create(**params)


def make_ap(articulo=None, articulo_s_revisar=None, proveedor=None, precio_de_lista=None, using="default", **kwargs):
    ArticuloProveedor = apps.get_model('articulos', 'ArticuloProveedor')
    prov = proveedor or make_proveedor(using=using)
    pl = precio_de_lista or make_precio_de_lista(proveedor=prov, using=using)
    params = dict(
        proveedor_id=prov.id,
        precio_de_lista_id=pl.id,
        codigo_proveedor=kwargs.pop('codigo_proveedor', '0007/'),
        descripcion_proveedor=kwargs.pop('descripcion_proveedor', 'AP'),
        precio=kwargs.pop('precio', 100),
        stock=kwargs.pop('stock', 1),
        dividir=kwargs.pop('dividir', False),
    )
    if articulo is not None:
        params['articulo_id'] = articulo.id
    if articulo_s_revisar is not None:
        params['articulo_s_revisar_id'] = articulo_s_revisar.id
    if 'descuento' in kwargs and kwargs['descuento'] is not None:
        params['descuento_id'] = kwargs['descuento'].id
    return ArticuloProveedor.objects.using(using).create(**params)


@pytest.mark.django_db(databases=['default'])
@override_settings(DEBUG_INFO=True)
def test_generar_precios_adds_debug_fields_on_base_and_asr():
    ArticuloSinRevisar = apps.get_model('articulos', 'ArticuloSinRevisar')
    asr = make_asr()
    # Use overrides to control inputs
    res = asr.generar_precios(cantidad=2, pago_efectivo=False, precio_de_lista=80, dividir=True, bulto=3, iva=10)
    assert isinstance(res, dict)
    # Debug extras must exist when DEBUG_INFO=True
    assert 'debug_bulto_articulo' in res and res['debug_bulto_articulo'] == 3
    assert 'debug_cantidad' in res and res['debug_cantidad'] == 2.0


@pytest.mark.django_db(databases=['default'])
def test_get_descuento_fallbacks_transient_without_db_row_and_from_ap():
    ArticuloSinRevisar = apps.get_model('articulos', 'ArticuloSinRevisar')
    Descuento = apps.get_model('precios', 'Descuento')

    # Ensure default DB has no "Sin Descuento" to trigger transient object path
    Descuento.objects.using('default').all().delete()

    asr = make_asr()
    d = asr.get_descuento()
    # Not persisted object (no pk) and with default fields
    assert d.pk is None and getattr(d, 'tipo', '') == 'Sin Descuento'

    # Now create an AP with its own active descuento and ensure ASR resolves it
    desc = ensure_descuento(tipo='Promo X', using='default', aplicar_umbral=False)
    ap = make_ap(articulo_s_revisar=asr, proveedor=None, descuento=desc)
    d2 = asr.get_descuento()
    assert d2 and d2.tipo == 'Promo X'


@pytest.mark.django_db(databases=['default'])
def test_articulo_generar_precios_without_ap_returns_error():
    Articulo = apps.get_model('articulos', 'Articulo')
    art = Articulo.objects.using('default').create(nombre='A', descripcion='d', codigo_barras='CB1')
    res = art.generar_precios(cantidad=1, pago_efectivo=False)
    assert isinstance(res, dict) and res.get('error')


@pytest.mark.django_db(databases=['default'])
def test_asr_save_normalizes_code_and_assigns_default_desc_when_exists():
    # Create default descuento in default DB so ASR.save assigns it
    sin_desc = ensure_descuento(using='default', aplicar_umbral=False)
    asr = make_asr(codigo_proveedor='00042')  # missing trailing slash on purpose
    # After save, codigo_proveedor normalized to '42/' and descuento set
    asr.refresh_from_db()
    assert asr.codigo_proveedor == '42/'
    assert asr.descuento_id == sin_desc.id


@pytest.mark.django_db(databases=['default'])
def test_asr_save_when_no_default_descuento_leaves_none_and_normalizes_non_numeric():
    Descuento = apps.get_model('precios', 'Descuento')
    Descuento.objects.using('default').all().delete()
    asr = make_asr(codigo_proveedor='ABC')
    asr.refresh_from_db()
    assert asr.codigo_proveedor == 'ABC/'
    assert asr.descuento_id is None


@pytest.mark.django_db(databases=['default'])
def test_asr_get_proveedor_ok_and_missing():
    ArticuloSinRevisar = apps.get_model('articulos', 'ArticuloSinRevisar')
    Proveedor = apps.get_model('proveedores', 'Proveedor')
    asr = make_asr()
    prov = asr.get_proveedor()
    assert prov and prov.id == asr.proveedor_id

    # Remove proveedor to trigger DoesNotExist branch
    Proveedor.objects.using('default').filter(pk=asr.proveedor_id).delete()
    assert asr.get_proveedor() is None


@pytest.mark.django_db(databases=['default'])
def test_ap_save_normalizes_code_and_get_codigo_completo():
    asr = make_asr(codigo_proveedor='0001/')
    ap = make_ap(articulo_s_revisar=asr, codigo_proveedor='00007')  # missing trailing slash
    ap.refresh_from_db()
    assert ap.codigo_proveedor == '7/'
    # get_codigo_completo appends proveedor.abreviatura
    assert ap.get_codigo_completo().endswith(f"/{ap.proveedor.abreviatura}")


@pytest.mark.django_db(databases=['default'])
def test_ap_generar_precios_uses_descuento_override_and_error_when_no_target():
    # descuento override branch (self.descuento present)
    asr = make_asr()
    desc = ensure_descuento(tipo='Desc AP', using='default', aplicar_umbral=False)
    ap = make_ap(articulo_s_revisar=asr, descuento=desc)
    res = ap.generar_precios(cantidad=2, pago_efectivo=True)
    assert isinstance(res, dict)
    # Build an unsaved AP with no target to trigger error path
    ArticuloProveedor = apps.get_model('articulos', 'ArticuloProveedor')
    pl = make_precio_de_lista(proveedor=None)
    ap2 = ArticuloProveedor(
        proveedor=pl.proveedor,
        precio_de_lista=pl,
        codigo_proveedor='1/',
        descripcion_proveedor='X',
        precio=100,
        stock=1,
        dividir=False,
    )
    res2 = ap2.generar_precios(cantidad=1, pago_efectivo=False)
    assert res2.get('error')


@pytest.mark.django_db(databases=['default'])
@override_settings(DEBUG_INFO=True)
def test_asr_generar_precios_respects_overrides_and_debug_keys():
    asr = make_asr(precio=200)
    res = asr.generar_precios(cantidad=1, pago_efectivo=False, precio_de_lista=50, dividir=True, bulto=5, iva=0)
    assert isinstance(res, dict)
    assert res.get('debug_bulto_articulo') == 5 and res.get('debug_cantidad') == 1.0
