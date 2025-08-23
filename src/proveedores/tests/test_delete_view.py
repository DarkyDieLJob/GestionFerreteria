import pytest
from django.urls import reverse
from proveedores.models import Proveedor


@pytest.mark.django_db
def test_proveedor_delete_view_deletes_and_redirects(client):
    prov = Proveedor.objects.create(nombre="Proveedor X", abreviatura="px")
    url = reverse("proveedores:proveedor_delete", kwargs={"pk": prov.pk})

    response = client.post(url, follow=True)

    # Redirige al listado
    assert response.redirect_chain, "Debe haber redirección tras eliminar"
    final_url = response.redirect_chain[-1][0]
    assert reverse("proveedores:proveedor_list") in final_url

    # El objeto fue eliminado
    assert not Proveedor.objects.filter(pk=prov.pk).exists()
