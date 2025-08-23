import pytest
from django.apps import apps

from articulos.adapters.repository import (
    _normalize_code_and_abbr,
    PrecioRepository,
    BusquedaRepository,
)


# Helpers

def _ensure_descuento_sin_descuento():
    Descuento = apps.get_model('precios', 'Descuento')
    if not Descuento.objects.using('negocio_db').filter(tipo='Sin Descuento').exists():
        Descuento.objects.using('negocio_db').create(tipo='Sin Descuento', aplicar_umbral=False)
    return Descuento.objects.using('negocio_db').get(tipo='Sin Descuento')


def _make_proveedor(**kwargs):
    Proveedor = apps.get_model('proveedores', 'Proveedor')
    n = Proveedor.objects.using('negocio_db').count() + 1
    defaults = dict(
        nombre=f'Prov SA {n}',
        abreviatura=f'PV{n}',
        descuento_comercial=0,
        margen_ganancia=1,
        margen_ganancia_efectivo=1,
    )
    defaults.update(kwargs)
    return Proveedor.objects.using('negocio_db').create(**defaults)


def _make_precio_de_lista(**kwargs):
    PrecioDeLista = apps.get_model('precios', 'PrecioDeLista')
    Proveedor = apps.get_model('proveedores', 'Proveedor')
    prov = kwargs.pop('proveedor', None) or _make_proveedor()
    return PrecioDeLista.objects.using('negocio_db').create(
        proveedor_id=prov.id,
        codigo=kwargs.pop('codigo', '1/'),
        descripcion=kwargs.pop('descripcion', 'PL'),
        precio=kwargs.pop('precio', 100),
        iva=kwargs.pop('iva', 21),
        bulto=kwargs.pop('bulto', 1),
        **kwargs,
    )


def _make_asr(**kwargs):
    ArticuloSinRevisar = apps.get_model('articulos', 'ArticuloSinRevisar')
    Descuento = apps.get_model('precios', 'Descuento')
    _ensure_descuento_sin_descuento()
    desc = Descuento.objects.using('negocio_db').first()
    Proveedor = apps.get_model('proveedores', 'Proveedor')
    prov = kwargs.pop('proveedor', None) or _make_proveedor()
    return ArticuloSinRevisar.objects.using('negocio_db').create(
        proveedor_id=prov.id,
        descuento_id=desc.id if desc else None,
        codigo_proveedor=kwargs.pop('codigo_proveedor', '0001/'),
        descripcion_proveedor=kwargs.pop('descripcion_proveedor', 'ASR'),
        precio=kwargs.pop('precio', 50),
        stock=kwargs.pop('stock', 1),
        estado=kwargs.pop('estado', 'pendiente'),
    )


def _make_ap(**kwargs):
    ArticuloProveedor = apps.get_model('articulos', 'ArticuloProveedor')
    Descuento = apps.get_model('precios', 'Descuento')
    _ensure_descuento_sin_descuento()
    desc = Descuento.objects.using('negocio_db').first()
    # Ensure we have a proveedor without triggering relation lookups
    prov = kwargs.pop('proveedor', None) or _make_proveedor()
    pl = kwargs.pop('precio_de_lista', None) or _make_precio_de_lista(proveedor=prov)
    asr = kwargs.pop('articulo_s_revisar', None) or _make_asr(proveedor=prov)
    return ArticuloProveedor.objects.using('negocio_db').create(
        articulo_s_revisar_id=asr.id,
        proveedor_id=prov.id,
        precio_de_lista_id=pl.id,
        codigo_proveedor=kwargs.pop('codigo_proveedor', '0001/'),
        descripcion_proveedor=kwargs.pop('descripcion_proveedor', 'AP'),
        precio=kwargs.pop('precio', 100),
        stock=kwargs.pop('stock', 1),
        dividir=kwargs.pop('dividir', False),
        descuento_id=(kwargs.pop('descuento', desc).id if desc else None),
    )


@pytest.mark.django_db(databases=['default', 'negocio_db'])
def test_normalize_code_and_abbr_cases():
    # abbr embedded and base with leading zeros, without trailing slash
    r1 = _normalize_code_and_abbr('00037/Vj')
    assert r1['code'] == '37/' and r1['abbr'] == 'VJ'

    # provided abreviatura should take precedence
    r2 = _normalize_code_and_abbr('00037/vj', 'pv')
    assert r2['code'] == '37/' and r2['abbr'] == 'PV'

    # already has trailing slash, no abbr
    r3 = _normalize_code_and_abbr('0042/')
    assert r3['code'] == '42/' and r3['abbr'] is None

    # non-numeric base preserved
    r4 = _normalize_code_and_abbr('ABC')
    assert r4['code'] == 'ABC/' and r4['abbr'] is None


@pytest.mark.django_db(transaction=True, databases=['default', 'negocio_db'])
def test_precio_repository_calcular_precios_for_ap_and_asr():
    ap = _make_ap()
    asr = _make_asr(proveedor=ap.proveedor)

    repo = PrecioRepository()
    res_ap = repo.calcular_precios(articulo_id=ap.id, tipo='articulo', cantidad=3, pago_efectivo=False)
    assert isinstance(res_ap, dict)
    assert 'final' in res_ap

    res_asr = repo.calcular_precios(articulo_id=asr.id, tipo='sin_revisar', cantidad=2, pago_efectivo=True)
    assert isinstance(res_asr, dict)
    assert 'final_efectivo' in res_asr


@pytest.mark.django_db(databases=['default', 'negocio_db'])
def test_precio_repository_invalid_tipo_raises():
    repo = PrecioRepository()
    with pytest.raises(ValueError):
        repo.calcular_precios(articulo_id=1, tipo='otro', cantidad=1, pago_efectivo=False)


@pytest.mark.django_db(transaction=True, databases=['default', 'negocio_db'])
def test_busqueda_repository_basic_search_with_abbr_filters():
    ap = _make_ap(codigo_proveedor='0001/')
    # ensure different proveedor/AP that should not match due to abbr filter
    _ = _make_ap(codigo_proveedor='0001/')

    repo = BusquedaRepository()
    # use the matching proveedor abreviatura
    Proveedor = apps.get_model('proveedores', 'Proveedor')
    abbr = Proveedor.objects.using('negocio_db').get(pk=ap.proveedor_id).abreviatura
    results = repo.buscar_articulos(query='0001', abreviatura=abbr.lower())
    assert isinstance(results, list) and len(results) >= 1
    item = results[0]
    # minimal fields present
    for key in ['codigo', 'proveedor', 'precios', 'puede_mapear']:
        assert key in item
    prov_val = item['proveedor']
    if isinstance(prov_val, dict):
        assert prov_val.get('abreviatura') == abbr
    else:
        assert str(prov_val).upper() == abbr.upper()
