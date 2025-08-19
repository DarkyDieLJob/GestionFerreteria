import pytest
from django.urls import reverse
from django.utils import timezone

from precios.adapters.models import Descuento
from precios.adapters.views import (
    DescuentoListView,
    DescuentoCreateView,
    DescuentoUpdateView,
    DescuentoDeleteView,
)
from precios.adapters.forms import DescuentoForm


@pytest.fixture
def descuento_factory():
    def _make(**overrides):
        defaults = {
            "tipo": "Descuento Test",
            "efectivo": False,
            "bulto": False,
            "cantidad_bulto": 1,
            "general": True,
            "temporal": False,
            "desde": None,
            "hasta": None,
        }
        defaults.update(overrides)
        return Descuento.objects.using("negocio_db").create(**defaults)

    return _make


@pytest.mark.django_db(databases=["negocio_db"])  # Base negocio_db
class TestDescuentoViews:
    def test_descuento_list_view_get(self, client, descuento_factory):
        d1 = descuento_factory(tipo="Alpha")
        d2 = descuento_factory(tipo="Beta")
        url = reverse("precios:descuento_list")

        resp = client.get(url)
        assert resp.status_code == 200
        # Debe listar ambos
        ctx_list = list(resp.context["descuentos"])  # context_object_name
        tipos = {d.tipo for d in ctx_list}
        assert {d1.tipo, d2.tipo}.issubset(tipos)

    def test_descuento_list_view_search(self, client, descuento_factory):
        descuento_factory(tipo="Promo Verano")
        descuento_factory(tipo="Invierno")
        url = reverse("precios:descuento_list")

        resp = client.get(url, {"q": "promo"})
        assert resp.status_code == 200
        ctx_list = list(resp.context["descuentos"])  # filtrado por 'q'
        assert len(ctx_list) == 1
        assert ctx_list[0].tipo == "Promo Verano"

    def test_descuento_create_view_get(self, client):
        url = reverse("precios:descuento_create")
        resp = client.get(url)
        assert resp.status_code == 200
        # Asegurar que el form está en el contexto
        assert isinstance(resp.context["form"], DescuentoForm)

    def test_descuento_create_view_post(self, client):
        url = reverse("precios:descuento_create")
        payload = {
            "tipo": "Promo X",
            "efectivo": "0",
            "bulto": "0",
            "cantidad_bulto": 1,
            "general": "0",
            "temporal": "",
            "desde": "",
            "hasta": "",
        }
        resp = client.post(url, data=payload)
        # Debe redirigir al listado
        assert resp.status_code == 302
        assert resp.headers.get("Location", "").endswith(reverse("precios:descuento_list"))

        # Verificar creación en negocio_db
        assert Descuento.objects.using("negocio_db").filter(tipo="Promo X").exists()

    def test_descuento_update_view_get(self, client, descuento_factory):
        d = descuento_factory(tipo="Original")
        url = reverse("precios:descuento_update", kwargs={"pk": d.pk})
        resp = client.get(url)
        assert resp.status_code == 200
        assert isinstance(resp.context["form"], DescuentoForm)

    def test_descuento_update_view_post(self, client, descuento_factory):
        d = descuento_factory(tipo="Original")
        url = reverse("precios:descuento_update", kwargs={"pk": d.pk})
        payload = {
            "tipo": "Modificado",
            "efectivo": "0.15",
            "bulto": "0",
            "cantidad_bulto": 2,
            "general": "0",
            "temporal": "",
            "desde": "",
            "hasta": "",
        }
        resp = client.post(url, data=payload)
        assert resp.status_code == 302
        assert resp.headers.get("Location", "").endswith(reverse("precios:descuento_list"))

        d_refreshed = Descuento.objects.using("negocio_db").get(pk=d.pk)
        assert d_refreshed.tipo == "Modificado"
        assert d_refreshed.cantidad_bulto == 2

    def test_descuento_delete_view_get(self, client, descuento_factory):
        d = descuento_factory()
        url = reverse("precios:descuento_delete", kwargs={"pk": d.pk})
        resp = client.get(url)
        assert resp.status_code == 200

    def test_descuento_delete_view_post(self, client, descuento_factory):
        d = descuento_factory()
        url = reverse("precios:descuento_delete", kwargs={"pk": d.pk})
        resp = client.post(url)
        assert resp.status_code == 302
        assert resp.headers.get("Location", "").endswith(reverse("precios:descuento_list"))
        assert not Descuento.objects.using("negocio_db").filter(pk=d.pk).exists()
