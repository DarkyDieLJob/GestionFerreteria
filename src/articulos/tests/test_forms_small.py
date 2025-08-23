import pytest
from django.apps import apps


@pytest.mark.django_db(transaction=True, databases=["default", "negocio_db"])
def test_edit_articulo_proveedor_form_handles_missing_related_precio_de_lista():
    Articulo = apps.get_model("articulos", "Articulo")
    Proveedor = apps.get_model("proveedores", "Proveedor")
    ArticuloProveedor = apps.get_model("articulos", "ArticuloProveedor")
    PrecioDeLista = apps.get_model("precios", "PrecioDeLista")

    # Crear base en negocio_db
    art = Articulo.objects.using("negocio_db").create(codigo_barras="A1", nombre="X")
    prov = Proveedor.objects.using("negocio_db").create(nombre="P1", abreviatura="P1")
    pl = PrecioDeLista.objects.using("negocio_db").create(
        proveedor_id=prov.id,
        codigo="001",
        descripcion="Item",
        precio=1,
        bulto=3,
    )

    ap = ArticuloProveedor.objects.using("negocio_db").create(
        articulo_id=art.id,
        proveedor_id=prov.id,
        precio_de_lista_id=pl.id,
        codigo_proveedor="001/",
        precio=1,
        stock=0,
    )

    # Borrar el PrecioDeLista para que acceder a ap.precio_de_lista lance DoesNotExist
    PrecioDeLista.objects.using("negocio_db").filter(id=pl.id).delete()

    from articulos.adapters.forms import EditArticuloProveedorForm

    form = EditArticuloProveedorForm(instance=ap)
    # Si el related falta, el formulario inicializa bulto=1 en el except
    assert form.fields["bulto"].initial == 1
