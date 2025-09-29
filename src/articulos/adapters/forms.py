"""
Formularios de la app "articulos" (capa de adaptadores).

Estos formularios ayudan a validar datos en las vistas, manteniendo el
acoplamiento con Django dentro de la capa de infraestructura y
permitiendo que el dominio permanezca libre de dependencias.
"""
from typing import List, Tuple

from django import forms
from django.apps import apps
from django.forms import ModelForm


class MapearArticuloForm(ModelForm):
    """
    Formulario para mapear un ArticuloSinRevisar hacia un Articulo.

    - Modelo base: Articulo
    - Campos: codigo_barras, descripcion
    - Campo adicional: articulo_id (ChoiceField) para seleccionar un Articulo
      existente o dejar vacío para crear uno nuevo.

    Se utiliza en la vista `mapear_articulo` para validar datos antes de
    ejecutar el caso de uso de mapeo.
    """

    articulo_id = forms.ChoiceField(
        required=False,
        choices=[],  # se completa dinámicamente en __init__
        label="Artículo existente (opcional)",
    )

    class Meta:
        model = apps.get_model("articulos", "Articulo")
        fields = ["codigo_barras", "descripcion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Articulo = apps.get_model("articulos", "Articulo")
        # Poblar choices con artículos existentes en la base de negocio
        opciones: List[Tuple[str, str]] = [("", "Crear nuevo")]
        for art in Articulo.objects.using("negocio_db").all()[:500]:
            etiqueta = f"{getattr(art, 'codigo_barras', '')} - {getattr(art, 'nombre', getattr(art, 'descripcion', ''))}"
            opciones.append((str(art.id), etiqueta))
        self.fields["articulo_id"].choices = opciones

        # Estilos Tailwind para widgets, alineados con core_auth
        base_input = {
            "class": "appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
        }
        self.fields["codigo_barras"].widget.attrs.update({
            **base_input,
            "placeholder": "Código de barras",
        })
        self.fields["descripcion"].widget.attrs.update({
            **base_input,
            "placeholder": "Descripción para publicación",
            "rows": 3,
        })
        self.fields["articulo_id"].widget.attrs.update({
            "class": "block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
        })
