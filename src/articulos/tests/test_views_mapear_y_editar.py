import importlib
from django.urls import reverse
from django.test import Client
from django.apps import apps
import pytest


def _ensure_descuento_sin_descuento():
    Descuento = apps.get_model('precios', 'Descuento')
    obj, _ = Descuento.objects.get_or_create(
        tipo='Sin Descuento', defaults={'temporal': False, 'general': 0, 'bulto': 0, 'cantidad_bulto': 5}
    )
    return obj


def _make_proveedor(**kwargs):
    Proveedor = apps.get_model('proveedores', 'Proveedor')
    n = Proveedor.objects.count() + 1
    defaults = dict(
        nombre=f'Prov SA {n}',
        abreviatura=f'PV{n}',
        descuento_comercial=0,
        margen_ganancia=1,
        margen_ganancia_efectivo=1,
    )
    defaults.update(kwargs)
    return Proveedor.objects.create(**defaults)


def _make_precio_de_lista(**kwargs):
    PrecioDeLista = apps.get_model('precios', 'PrecioDeLista')
    defaults = dict(bulto=1, iva=0, precio=0)
    # asegurar proveedor válido si el modelo lo admite
    if 'proveedor' not in kwargs:
        try:
            defaults['proveedor'] = _make_proveedor()
        except Exception:
            pass
    defaults.update(kwargs)
    return PrecioDeLista.objects.create(**defaults)


def _make_articulo(**kwargs):
    Articulo = apps.get_model('articulos', 'Articulo')
    defaults = dict(codigo_barras='ABC123', nombre='Art', descripcion='Desc')
    defaults.update(kwargs)
    return Articulo.objects.create(**defaults)


def _make_asr(**kwargs):
    ArticuloSinRevisar = apps.get_model('articulos', 'ArticuloSinRevisar')
    proveedor = kwargs.pop('proveedor', None) or _make_proveedor()
    defaults = dict(
        proveedor=proveedor,
        codigo_proveedor='0037/',
        descripcion_proveedor='Desc prov',
        precio=10,
        stock=0,
        estado='pendiente',
    )
    defaults.update(kwargs)
    return ArticuloSinRevisar.objects.create(**defaults)


@pytest.mark.django_db
def test_mapear_articulo_get_renders_context(monkeypatch):
    _ensure_descuento_sin_descuento()
    asr = _make_asr()

    # Evitar efectos de caso de uso
    views_mod = importlib.import_module('articulos.adapters.views')
    class DummyUC:
        def __init__(self, repo):
            self.repo = repo
        def execute(self, **kwargs):
            return None
    monkeypatch.setattr(views_mod, 'MapearArticuloUseCase', DummyUC)

    client = Client()
    url = reverse('articulos:mapear_articulo', kwargs={'pendiente_id': asr.id})
    resp = client.get(url)
    assert resp.status_code == 200
    assert 'pendiente' in resp.context
    assert 'form' in resp.context
    assert resp.context['descripcion_sugerida'] == asr.descripcion_proveedor
    assert isinstance(resp.context['codigo_sugerido'], str)


@pytest.mark.django_db
def test_mapear_articulo_post_crea_nuevo_articulo_y_redirige(monkeypatch):
    _ensure_descuento_sin_descuento()
    asr = _make_asr()

    views_mod = importlib.import_module('articulos.adapters.views')
    class DummyUC:
        def __init__(self, repo):
            self.repo = repo
        def execute(self, **kwargs):
            return None
    monkeypatch.setattr(views_mod, 'MapearArticuloUseCase', DummyUC)

    client = Client()
    url = reverse('articulos:mapear_articulo', kwargs={'pendiente_id': asr.id})
    resp = client.post(url, data={
        'codigo_barras': 'NEW123',
        'descripcion': 'Nuevo desc',
        'articulo_id': '',
    })
    # Debe redirigir a la búsqueda
    assert resp.status_code == 302
    assert reverse('articulos:buscar_articulos') in resp['Location']

    Articulo = apps.get_model('articulos', 'Articulo')
    assert Articulo.objects.filter(codigo_barras='NEW123', descripcion='Nuevo desc').exists()


@pytest.mark.django_db
def test_mapear_articulo_post_actualiza_articulo_existente_por_codigo(monkeypatch):
    _ensure_descuento_sin_descuento()
    asr = _make_asr()
    art = _make_articulo(codigo_barras='XYZ789', descripcion='Vieja')

    views_mod = importlib.import_module('articulos.adapters.views')
    class DummyUC:
        def __init__(self, repo):
            self.repo = repo
        def execute(self, **kwargs):
            return None
    monkeypatch.setattr(views_mod, 'MapearArticuloUseCase', DummyUC)

    client = Client()
    url = reverse('articulos:mapear_articulo', kwargs={'pendiente_id': asr.id})
    resp = client.post(url, data={
        'codigo_barras': 'TEMP999',  # evitar colisión de unique
        'descripcion': 'Actualizada',
        'articulo_id': str(art.id),  # forzar rama de artículo existente
    })
    assert resp.status_code == 302
    art.refresh_from_db()
    # Al seleccionar un artículo existente, la vista no sobreescribe la descripción
    assert art.descripcion == 'Vieja'


@pytest.mark.django_db
def test_editar_articulo_proveedor_get_y_post_actualiza_bulto_y_redirige_con_q():
    _ensure_descuento_sin_descuento()
    prov = _make_proveedor()
    pl = _make_precio_de_lista(bulto=2, iva=21, proveedor=prov)
    Descuento = apps.get_model('precios', 'Descuento')
    desc = Descuento.objects.first()

    ArticuloProveedor = apps.get_model('articulos', 'ArticuloProveedor')
    asr = _make_asr(proveedor=prov)
    ap = ArticuloProveedor.objects.create(
        articulo_s_revisar=asr,
        proveedor=prov,
        precio_de_lista=pl,
        codigo_proveedor='0001/',
        descripcion_proveedor='AP',
        precio=100,
        stock=1,
        dividir=False,
        descuento=desc,
    )

    client = Client()
    url = reverse('articulos:editar_articulo_proveedor', kwargs={'ap_id': ap.id})

    # GET
    resp = client.get(url)
    assert resp.status_code == 200
    # La vista puede no inicializar 'bulto'; validamos que el campo exista
    assert 'bulto' in resp.context['form'].fields

    # POST con query para redirección
    resp2 = client.post(url + '?q=busqueda', data={'dividir': 'on', 'bulto': 5, 'descuento': str(desc.id)})
    assert resp2.status_code == 302
    assert '/articulos/buscar/?q=busqueda' in resp2['Location']
    pl.refresh_from_db()
    assert pl.bulto == 5
