from django.urls import path

from importaciones.adapters.views import (
    ImportacionCreateView,
    ImportacionPreviewView,
    ImportacionesLandingView,
    ConfigImportacionDetailView,
    ArchivoPendienteDeleteView,
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
    # API: Detalle de configuración por proveedor (JSON)
    path(
        "api/configuracion/<int:proveedor_id>/",
        ConfigImportacionDetailView.as_view(),
        name="config_detail",
    ),
    # Vista de confirmación (muestra pendientes encolados para el proveedor)
    path(
        "confirmar/<int:proveedor_id>/",
        ImportacionCreateView.as_view(),
        name="importacion_create",
    ),
    # Eliminar pendiente
    path(
        "pendiente/<int:proveedor_id>/<int:pendiente_id>/eliminar/",
        ArchivoPendienteDeleteView.as_view(),
        name="pendiente_delete",
    ),
]

# Nota: este archivo está listo para ser incluido en core_config/urls.py como:
#   path("", include("importaciones.urls"))
