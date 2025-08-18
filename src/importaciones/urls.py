from django.urls import path

from importaciones.adapters.views import (
    ImportacionCreateView,
    ImportacionPreviewView,
)

# Namespace para esta app, útil para usar reverse('importaciones:...')
app_name = "importaciones"

urlpatterns = [
    # Subir un archivo Excel para un proveedor específico.
    # Uso en reverse: reverse('importaciones:importacion_create', kwargs={'proveedor_id': 123})
    path(
        "crear/<int:proveedor_id>/",
        ImportacionCreateView.as_view(),
        name="importacion_create",
    ),
    # Mostrar la vista previa del Excel subido para un proveedor y un nombre de archivo dados.
    # Uso en reverse: reverse('importaciones:importacion_preview', kwargs={'proveedor_id': 123, 'nombre_archivo': 'archivo.xlsx'})
    path(
        "vista-previa/<int:proveedor_id>/<str:nombre_archivo>/",
        ImportacionPreviewView.as_view(),
        name="importacion_preview",
    ),
]

# Nota: este archivo está listo para ser incluido en core_config/urls.py como:
#   path("", include("importaciones.urls"))
