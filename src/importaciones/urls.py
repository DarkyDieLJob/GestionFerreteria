from django.urls import path

from importaciones.adapters.views import (
    ImportacionCreateView,
    ImportacionPreviewView,
    ImportacionesLandingView,
)

# Namespace para esta app, útil para usar reverse('importaciones:...')
app_name = "importaciones"

urlpatterns = [
    # Landing para seleccionar proveedor y comenzar importación
    path(
        "",
        ImportacionesLandingView.as_view(),
        name="landing",
    ),
    # Vista de previsualización del Excel subido (elige hojas/configs)
    path(
        "vista-previa/<int:proveedor_id>/<str:nombre_archivo>/",
        ImportacionPreviewView.as_view(),
        name="importacion_preview",
    ),
    # Vista de confirmación (muestra pendientes encolados para el proveedor)
    path(
        "confirmar/<int:proveedor_id>/",
        ImportacionCreateView.as_view(),
        name="importacion_create",
    ),
]

# Nota: este archivo está listo para ser incluido en core_config/urls.py como:
#   path("", include("importaciones.urls"))
