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


class EditArticuloProveedorForm(ModelForm):
    """
    Formulario para editar datos del ArticuloProveedor y su PrecioDeLista relacionado.

    - Modelo base: ArticuloProveedor
    - Campos model: dividir, descuento
    - Campo extra (no model): bulto (se guarda en ap.precio_de_lista.bulto)
    """

    bulto = forms.IntegerField(min_value=1, label="Cantidad por bulto")

    class Meta:
        model = apps.get_model("articulos", "ArticuloProveedor")
        fields = ["dividir", "descuento"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Descuento = apps.get_model("precios", "Descuento")
        # Poblamos el queryset de descuento y set de widgets
        self.fields["descuento"].queryset = Descuento.objects.using("negocio_db").all()
        self.fields["descuento"].required = False

        # Inicializamos bulto desde el PrecioDeLista relacionado
        if self.instance and getattr(self.instance, "precio_de_lista_id", None):
            try:
                pl = self.instance.precio_de_lista
                self.fields["bulto"].initial = getattr(pl, "bulto", 1) or 1
            except Exception:
                self.fields["bulto"].initial = 1

        # Estilos Tailwind
        base_input = {
            "class": "appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
        }
        self.fields["bulto"].widget.attrs.update({**base_input, "placeholder": "Cantidad por bulto"})
        if "descuento" in self.fields:
            self.fields["descuento"].widget.attrs.update({
                "class": "block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
            })
        if "dividir" in self.fields:
            # Checkbox estilizado básico
            self.fields["dividir"].widget.attrs.update({
                "class": "h-4 w-4 text-indigo-600 border-gray-300 rounded",
            })

    def save(self, commit=True):
        ap = super().save(commit=False)
        # Guardar bulto en el PrecioDeLista relacionado
        bulto_val = self.cleaned_data.get("bulto")
        if bulto_val and getattr(ap, "precio_de_lista_id", None):
            pl = ap.precio_de_lista
            if getattr(pl, "bulto", None) != bulto_val:
                pl.bulto = bulto_val
                pl.save(using="negocio_db")
        if commit:
            ap.save(using="negocio_db")
        return ap
