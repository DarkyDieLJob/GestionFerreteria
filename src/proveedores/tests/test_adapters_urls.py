import importlib


def test_import_proveedores_adapters_urls_executes_module():
    mod = importlib.import_module('proveedores.adapters.urls')
    assert getattr(mod, 'app_name', None) == 'proveedores'
    urlpatterns = getattr(mod, 'urlpatterns', None)
    assert isinstance(urlpatterns, list)
