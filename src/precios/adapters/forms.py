"""
Formularios de la app precios (capa adapters).

Este módulo define formularios ModelForm para trabajar con los modelos de precios.
El formulario DescuentoForm se utiliza en las vistas DescuentoCreateView y
DescuentoUpdateView para validar y serializar datos del modelo Descuento.
"""

from django import forms
from django.core.exceptions import ValidationError

from precios.adapters.models import Descuento


class DescuentoForm(forms.ModelForm):
    """Formulario para crear/editar instancias de Descuento.

    Validaciones incluidas:
    - tipo: máximo 50 caracteres.
    - cantidad_bulto: entero positivo.

    Nota: Este form está pensado para usarse en DescuentoCreateView y
    DescuentoUpdateView.
    """

    class Meta:
        model = Descuento
        fields = [
            "tipo",
            "efectivo",
            "bulto",
            "cantidad_bulto",
            "general",
            "temporal",
            "desde",
            "hasta",
        ]
        widgets = {
            # Activar selector nativo de fecha en navegadores (HTML5)
            "desde": forms.DateInput(attrs={"type": "date", "class": "w-full"}),
            "hasta": forms.DateInput(attrs={"type": "date", "class": "w-full"}),
        }

    def clean_tipo(self):
        valor = (self.cleaned_data.get("tipo") or "").strip()
        if len(valor) > 50:
            raise ValidationError("El tipo no puede exceder 50 caracteres.")
        return valor

    def clean_cantidad_bulto(self):
        valor = self.cleaned_data.get("cantidad_bulto")
        if valor is None:
            return valor
        # Asegurar entero y positivo
        try:
            valor_int = int(valor)
        except (TypeError, ValueError):
            raise ValidationError("cantidad_bulto debe ser un número entero.")
        if valor_int <= 0:
            raise ValidationError("cantidad_bulto debe ser un entero positivo.")
        return valor_int
