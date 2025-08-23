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
        if not valor:
            raise ValidationError("El tipo es obligatorio.")
        if len(valor) > 50:
            raise ValidationError("El tipo no puede exceder 50 caracteres.")
        return valor

    def clean_cantidad_bulto(self):
        valor = self.cleaned_data.get("cantidad_bulto")
        if valor is None:
            return valor
        # Tratar cadenas vacías/whitespace como valor ausente
        if isinstance(valor, str) and not valor.strip():
            return None
        # Asegurar entero y positivo
        try:
            valor_int = int(valor)
        except (TypeError, ValueError):
            raise ValidationError("cantidad_bulto debe ser un número entero.")
        if valor_int <= 0:
            raise ValidationError("cantidad_bulto debe ser un entero positivo.")
        return valor_int

    def clean(self):
        cleaned = super().clean()
        bulto = cleaned.get("bulto")
        cantidad_bulto = cleaned.get("cantidad_bulto")
        # Si es un descuento por bulto, la cantidad es obligatoria
        if bulto:
            if not cantidad_bulto:
                self.add_error("cantidad_bulto", "Requerido cuando 'bulto' está activo.")
        else:
            # Si no es por bulto, no anulamos el valor (el campo no admite null).
            # Preservar el existente en instancia o aplicar el default del modelo si viene vacío.
            if not cantidad_bulto:
                try:
                    # valor actual de la instancia si existe
                    current = getattr(self.instance, "cantidad_bulto", None)
                    if current:
                        cleaned["cantidad_bulto"] = int(current)
                    else:
                        default = Descuento._meta.get_field("cantidad_bulto").default
                        cleaned["cantidad_bulto"] = int(default)
                except Exception:
                    # fallback seguro
                    cleaned["cantidad_bulto"] = 1
        return cleaned

