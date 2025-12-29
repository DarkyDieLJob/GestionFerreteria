"""
Formularios para la app proveedores.

Este módulo define formularios basados en ModelForm para la entidad Proveedor.
El formulario principal (ProveedorForm) se utiliza en ProveedorCreateView y
ProveedorUpdateView para validar y normalizar datos antes de persistir en la BD
('negocio_db' es gestionado por las vistas).
"""
from django import forms
from django.core.exceptions import ValidationError

from proveedores.models import Proveedor


class ProveedorForm(forms.ModelForm):
    """Formulario de Proveedor con validación de abreviatura.

    Reglas de 'abreviatura':
    - Máximo 3 caracteres
    - Solo letras (A-Z)
    - Se normaliza a mayúsculas automáticamente

    Este form está pensado para usarse en ProveedorCreateView y ProveedorUpdateView.
    """

    class Meta:
        model = Proveedor
        fields = [
            "nombre",
            "abreviatura",
            "descuento_comercial",
            "margen_ganancia",
            "margen_ganancia_efectivo",
            "margen_ganancia_bulto",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm px-3 py-2",
                "placeholder": "Nombre del proveedor",
                "autocomplete": "off",
            }),
            "abreviatura": forms.TextInput(attrs={
                "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm px-3 py-2 uppercase",
                "maxlength": 3,
                "placeholder": "ABC",
                "autocomplete": "off",
            }),
            "descuento_comercial": forms.NumberInput(attrs={
                "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm px-3 py-2",
                "step": "0.01",
                "min": "0",
            }),
            "margen_ganancia": forms.NumberInput(attrs={
                "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm px-3 py-2",
                "step": "0.01",
                "min": "0",
            }),
            "margen_ganancia_efectivo": forms.NumberInput(attrs={
                "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm px-3 py-2",
                "step": "0.01",
                "min": "0",
            }),
            "margen_ganancia_bulto": forms.NumberInput(attrs={
                "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm px-3 py-2",
                "step": "0.01",
                "min": "0",
            }),
        }

    def clean_abreviatura(self):
        value = (self.cleaned_data.get("abreviatura") or "").strip().upper()
        if not value:
            raise ValidationError("La abreviatura es obligatoria.")
        if len(value) > 3:
            raise ValidationError("La abreviatura debe tener como máximo 3 caracteres.")
        # Permitir letras y números (A-Z, 0-9)
        if not value.isalnum():
            raise ValidationError("La abreviatura solo puede contener letras y números (A-Z, 0-9).")
        return value
