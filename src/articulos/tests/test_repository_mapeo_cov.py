import pytest
from django.apps import apps

from articulos.adapters.repository import MapeoRepository


def _ensure_descuento_sin_descuento(using='negocio_db'):
    Descuento = apps.get_model('precios', 'Descuento')
    obj, _ = Descuento.objects.using(using).get_or_create(
        tipo='Sin Descuento', defaults={'aplicar_umbral': False}
    )
    return obj


def _make_proveedor(using='negocio_db', **kwargs):
    Proveedor = apps.get_model('proveedores', 'Proveedor')
    n = Proveedor.objects.using(using).count() + 1
    defaults = dict(
        nombre=f'Prov SA {n}', abreviatura=f'PV{n}', descuento_comercial=0, margen_ganancia=1, margen_ganancia_efectivo=1
    )
    defaults.update(kwargs)
    return Proveedor.objects.using(using).create(**defaults)


def _make_precio_de_lista(proveedor=None, using='negocio_db', **kwargs):
    PrecioDeLista = apps.get_model('precios', 'PrecioDeLista')
    prov = proveedor or _make_proveedor(using=using)
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


def _make_asr(proveedor=None, using='negocio_db', **kwargs):
    ArticuloSinRevisar = apps.get_model('articulos', 'ArticuloSinRevisar')
    _ensure_descuento_sin_descuento(using=using)
    prov = proveedor or _make_proveedor(using=using)
    params = dict(
        proveedor_id=prov.id,
        codigo_proveedor=kwargs.pop('codigo_proveedor', '0001/'),
        descripcion_proveedor=kwargs.pop('descripcion_proveedor', 'ASR'),
        precio=kwargs.pop('precio', 50),
        stock=kwargs.pop('stock', 1),
        estado=kwargs.pop('estado', 'pendiente'),
    )
    params.update(kwargs)
    return ArticuloSinRevisar.objects.using(using).create(**params)


def _make_articulo(using='negocio_db', **kwargs):
    Articulo = apps.get_model('articulos', 'Articulo')
    params = dict(
        nombre=kwargs.pop('nombre', 'Art 1'),
        descripcion=kwargs.pop('descripcion', 'D'),
        codigo_barras=kwargs.pop('codigo_barras', 'CB-1'),
    )
    params.update(kwargs)
    return Articulo.objects.using(using).create(**params)


def _make_ap(articulo=None, articulo_s_revisar=None, proveedor=None, precio_de_lista=None, using='negocio_db', **kwargs):
    ArticuloProveedor = apps.get_model('articulos', 'ArticuloProveedor')
    _ensure_descuento_sin_descuento(using=using)
    prov = proveedor or _make_proveedor(using=using)
    pl = precio_de_lista or _make_precio_de_lista(proveedor=prov, using=using)
    params = dict(
        proveedor_id=prov.id,
        precio_de_lista_id=pl.id,
        codigo_proveedor=kwargs.pop('codigo_proveedor', '0001/'),
        descripcion_proveedor=kwargs.pop('descripcion_proveedor', 'AP'),
        precio=kwargs.pop('precio', 100),
        stock=kwargs.pop('stock', 1),
        dividir=kwargs.pop('dividir', False),
    )
    if articulo is not None:
        params['articulo_id'] = articulo.id
    if articulo_s_revisar is not None:
        params['articulo_s_revisar_id'] = articulo_s_revisar.id
    return ArticuloProveedor.objects.using(using).create(**params)


@pytest.mark.django_db(transaction=True, databases=['default', 'negocio_db'])
def test_mapeo_repository_mapear_articulo_updates_relations_and_dedups_and_marks_asr():
    # Arrange: ASR with multiple APs sharing the same PrecioDeLista (duplicates)
    prov = _make_proveedor()
    pl = _make_precio_de_lista(proveedor=prov)
    asr = _make_asr(proveedor=prov)
    # Create two APs with different PrecioDeLista (unique constraint prevents duplicates per PL)
    ap1 = _make_ap(articulo_s_revisar=asr, proveedor=prov, precio_de_lista=pl, codigo_proveedor='0001/')
    pl2 = _make_precio_de_lista(proveedor=prov, codigo='2/')
    ap2 = _make_ap(articulo_s_revisar=asr, proveedor=prov, precio_de_lista=pl2, codigo_proveedor='0002/')

    art = _make_articulo()

    # Act
    repo = MapeoRepository()
    res = repo.mapear_articulo(articulo_s_revisar_id=asr.id, articulo_id=art.id)

    # Assert status and ids
    assert res['status'] == 'ok' and res['articulo_s_revisar_id'] == asr.id and res['articulo_id'] == art.id

    ArticuloProveedor = apps.get_model('articulos', 'ArticuloProveedor')
    # All APs for the ASR must now point to the articulo, and ASR link removed
    for ap in ArticuloProveedor.objects.using('negocio_db').all():
        assert ap.articulo_id == art.id
        assert ap.articulo_s_revisar_id is None

    # There should be exactly 2 APs (one per each distinct precio_de_lista)
    assert ArticuloProveedor.objects.using('negocio_db').count() == 2

    # ASR marked as mapeado with fecha_mapeo set
    ArticuloSinRevisar = apps.get_model('articulos', 'ArticuloSinRevisar')
    asr_db = ArticuloSinRevisar.objects.using('negocio_db').get(pk=asr.id)
    assert asr_db.estado == 'mapeado' and asr_db.fecha_mapeo is not None
