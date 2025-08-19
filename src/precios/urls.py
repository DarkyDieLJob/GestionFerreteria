"""
URLs for the precios app.

This module registers the URL patterns for discount-related views.
It is designed to be included from core_config/urls.py via:
    path("precios/", include("precios.urls"))

Names are namespaced under 'precios' so you can reverse like:
    reverse('precios:descuento_list')
"""

from django.urls import path

# Import views from the adapters layer of the precios app
from precios.adapters.views import (
    DescuentoListView,
    DescuentoCreateView,
    DescuentoUpdateView,
    DescuentoDeleteView,
)

# Namespace for URL reversing: reverse('precios:...')
app_name = "precios"

urlpatterns = [
    # Listado de descuentos
    # Ejemplo de reverse: reverse('precios:descuento_list')
    path("", DescuentoListView.as_view(), name="descuento_list"),

    # Crear un nuevo descuento
    # Ejemplo de reverse: reverse('precios:descuento_create')
    path("crear/", DescuentoCreateView.as_view(), name="descuento_create"),

    # Editar un descuento existente, identificado por su PK (entero)
    # Ejemplo de reverse: reverse('precios:descuento_update', kwargs={'pk': 1})
    path("<int:pk>/editar/", DescuentoUpdateView.as_view(), name="descuento_update"),

    # Eliminar un descuento existente, identificado por su PK (entero)
    # Ejemplo de reverse: reverse('precios:descuento_delete', kwargs={'pk': 1})
    path("<int:pk>/eliminar/", DescuentoDeleteView.as_view(), name="descuento_delete"),
]
