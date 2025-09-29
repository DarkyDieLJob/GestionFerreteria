import importlib
import types
from django.test import RequestFactory


def test_import_articulos_adapters_urls_executes_module():
    mod = importlib.import_module('articulos.adapters.urls')
    assert getattr(mod, 'app_name', None) == 'articulos'
    urlpatterns = getattr(mod, 'urlpatterns', None)
    assert isinstance(urlpatterns, list)


def test_buscar_articulo_view_queryset_and_context(monkeypatch):
    views_mod = importlib.import_module('articulos.adapters.views')

    class DummyUseCase:
        def __init__(self, repo):
            self.repo = repo
        def execute(self, *, query):
            # devolver lista vacía para simplificar
            return []

    class DummyRepo:  # no se usa realmente, pero satisface la firma
        pass

    # Reemplazar dependencias en el módulo de vistas
    monkeypatch.setattr(views_mod, 'BuscarArticuloUseCase', DummyUseCase)
    monkeypatch.setattr(views_mod, 'BusquedaRepository', DummyRepo)

    rf = RequestFactory()
    request = rf.get('/articulos/buscar/?q=')

    view = views_mod.BuscarArticuloView()
    view.setup(request)

    qs = view.get_queryset()
    assert isinstance(qs, list) and qs == []

    # ListView.get_context_data requiere object_list en llamadas directas
    ctx = view.get_context_data(object_list=qs)
    assert ctx.get('query') == ''
