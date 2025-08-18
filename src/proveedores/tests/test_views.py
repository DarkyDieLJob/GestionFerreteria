import pytest
from django.urls import reverse

from proveedores.adapters.models import Proveedor


@pytest.fixture
@pytest.mark.django_db(databases=["negocio_db"])
def proveedor_factory():
    def _make(**kwargs):
        defaults = {
            "nombre": "Proveedor Demo",
            "abreviatura": "PRV",
            "descuento_comercial": 0,
            "margen_ganancia": 10,
            "margen_ganancia_efectivo": 8,
            "margen_ganancia_bulto": 12,
        }
        defaults.update(kwargs)
        obj = Proveedor(**defaults)
        obj.save(using="negocio_db")
        return obj

    return _make


# -------------------------------
# ProveedorListView
# -------------------------------
@pytest.mark.django_db(databases=["negocio_db"])
def test_proveedor_list_view_get(client, proveedor_factory):
    p1 = proveedor_factory(nombre="Acme S.A.", abreviatura="ACM")
    p2 = proveedor_factory(nombre="Beta Corp", abreviatura="BTC")

    url = reverse("proveedores:proveedor_list")
    resp = client.get(url)
    assert resp.status_code == 200
    # contexto y contenido
    proveedores = resp.context["proveedores"]
    nombres = {p.nombre for p in proveedores}
    assert {"Acme S.A.", "Beta Corp"}.issubset(nombres)


@pytest.mark.django_db(databases=["negocio_db"])
def test_proveedor_list_view_search_by_name(client, proveedor_factory):
    proveedor_factory(nombre="FerreMax", abreviatura="FMX")
    proveedor_factory(nombre="Tornillos SRL", abreviatura="TRN")

    url = reverse("proveedores:proveedor_list")
    resp = client.get(url, {"q": "ferre"})
    assert resp.status_code == 200
    resultados = list(resp.context["proveedores"])
    assert len(resultados) == 1
    assert resultados[0].nombre == "FerreMax"


@pytest.mark.django_db(databases=["negocio_db"])
def test_proveedor_list_view_search_by_abreviatura(client, proveedor_factory):
    proveedor_factory(nombre="Proveedor Uno", abreviatura="UNO")
    proveedor_factory(nombre="Proveedor Dos", abreviatura="DOS")

    url = reverse("proveedores:proveedor_list")
    resp = client.get(url, {"q": "dos"})
    assert resp.status_code == 200
    resultados = list(resp.context["proveedores"])
    assert len(resultados) == 1
    assert resultados[0].abreviatura == "DOS"


# -------------------------------
# ProveedorCreateView
# -------------------------------
@pytest.mark.django_db(databases=["negocio_db"])
def test_proveedor_create_view_get(client):
    url = reverse("proveedores:proveedor_create")
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"Guardar" in resp.content


@pytest.mark.django_db(databases=["negocio_db"])
def test_proveedor_create_view_post(client):
    url = reverse("proveedores:proveedor_create")
    data = {
        "nombre": "Nuevo Prov",
        "abreviatura": "NPV",
        "descuento_comercial": "0",
        "margen_ganancia": "15",
        "margen_ganancia_efectivo": "10",
        "margen_ganancia_bulto": "20",
    }
    resp = client.post(url, data)
    assert resp.status_code == 302
    assert resp.headers.get("Location").endswith(reverse("proveedores:proveedor_list"))

    # Verificar creación en negocio_db
    assert Proveedor.objects.using("negocio_db").filter(nombre="Nuevo Prov").exists()


# -------------------------------
# ProveedorUpdateView
# -------------------------------
@pytest.mark.django_db(databases=["negocio_db"])
def test_proveedor_update_view_get_and_post(client, proveedor_factory):
    prov = proveedor_factory(nombre="Cambio SA", abreviatura="CAM")

    # GET
    url = reverse("proveedores:proveedor_update", args=[prov.pk])
    resp = client.get(url)
    assert resp.status_code == 200

    # POST (actualizar)
    data = {
        "nombre": "Cambio SA Updated",
        "abreviatura": "CAM",
        "descuento_comercial": "5",
        "margen_ganancia": "18",
        "margen_ganancia_efectivo": "12",
        "margen_ganancia_bulto": "22",
    }
    resp = client.post(url, data)
    assert resp.status_code == 302
    assert resp.headers.get("Location").endswith(reverse("proveedores:proveedor_list"))

    refreshed = Proveedor.objects.using("negocio_db").get(pk=prov.pk)
    assert refreshed.nombre == "Cambio SA Updated"
    assert str(refreshed.margen_ganancia) in {"18", "18.00"}


# -------------------------------
# ProveedorDeleteView
# -------------------------------
@pytest.mark.django_db(databases=["negocio_db"])
def test_proveedor_delete_view_get_and_post(client, proveedor_factory):
    prov = proveedor_factory(nombre="DeleteMe", abreviatura="DEL")
    url = reverse("proveedores:proveedor_delete", args=[prov.pk])

    # GET de confirmación
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"Eliminar" in resp.content

    # POST de eliminación
    resp = client.post(url)
    assert resp.status_code == 302
    assert resp.headers.get("Location").endswith(reverse("proveedores:proveedor_list"))

    assert not Proveedor.objects.using("negocio_db").filter(pk=prov.pk).exists()
