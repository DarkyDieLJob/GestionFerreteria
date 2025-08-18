"""
URLs de la app "articulos".

Incluir en core_config/urls.py con:
    path("articulos/", include("articulos.urls"))

Los nombres de las rutas se usan para reverse, por ejemplo:
    reverse('articulos:buscar_articulos')
    reverse('articulos:mapear_articulo', kwargs={'pendiente_id': 123})
"""
from django.urls import path
from articulos.adapters.views import (
    BuscarArticuloView,
    mapear_articulo,  # vista de función para el mapeo
)

# Namespace de la app para usar con reverse('articulos:...')
app_name = "articulos"

urlpatterns = [
    # Búsqueda de artículos (vista basada en clase)
    # Uso: reverse('articulos:buscar_articulos') -> "/articulos/buscar/"
    path("buscar/", BuscarArticuloView.as_view(), name="buscar_articulos"),

    # Mapeo de ArticuloSinRevisar -> Articulo (vista de función)
    # Nota: el convertidor correcto en Django es <int:pendiente_id>
    # Uso: reverse('articulos:mapear_articulo', kwargs={'pendiente_id': 1}) -> "/articulos/mapear/1/"
    # Integración con forms: la vista `mapear_articulo` utiliza `MapearArticuloForm`
    # para validar datos del POST (codigo_barras, descripcion y articulo_id) y
    # renderizar errores en GET/POST. La URL permanece igual; solo cambia la
    # lógica interna de validación en la vista.
    path("mapear/<int:pendiente_id>/", mapear_articulo, name="mapear_articulo"),
]
