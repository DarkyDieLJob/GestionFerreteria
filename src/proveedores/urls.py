"""
URLs de la aplicación proveedores.

Listo para incluirse en core_config/urls.py con:
    path('proveedores/', include('proveedores.urls'))
"""
from django.urls import path

from proveedores.adapters.views import (
    ProveedorListView,
    ProveedorCreateView,
    ProveedorUpdateView,
    ProveedorDeleteView,
)

app_name = "proveedores"

# Nota: Los nombres de las rutas (name=...) se usan para reverse, e.g.:
#   reverse('proveedores:proveedor_list')
#   reverse('proveedores:proveedor_create')
#   reverse('proveedores:proveedor_update', kwargs={'pk': 1})
#   reverse('proveedores:proveedor_delete', kwargs={'pk': 1})
urlpatterns = [
    # Lista de proveedores
    # URL raíz de la app. Muestra el listado de proveedores.
    path("", ProveedorListView.as_view(), name="proveedor_list"),

    # Crear proveedor
    # Muestra un formulario para crear un nuevo proveedor.
    path("crear/", ProveedorCreateView.as_view(), name="proveedor_create"),

    # Editar proveedor
    # Recibe el identificador del proveedor a editar.
    path("<int:pk>/editar/", ProveedorUpdateView.as_view(), name="proveedor_update"),

    # Eliminar proveedor
    # Recibe el identificador del proveedor a eliminar.
    path("<int:pk>/eliminar/", ProveedorDeleteView.as_view(), name="proveedor_delete"),
]
