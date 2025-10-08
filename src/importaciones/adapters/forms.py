"""
Formularios para la app de importaciones.

Este formulario se utiliza en la vista ImportacionCreateView para subir
archivos de Excel/hojas de cálculo. Se valida que la extensión sea una
permitida (.xlsx, .xls, .ods, .csv).
"""
from django import forms
import os


class ImportacionForm(forms.Form):
    """Formulario para subir un archivo de importación.

    Se usa en ImportacionCreateView para permitir al usuario subir un
    archivo de Excel/hoja de cálculo que luego será procesado por el
    repositorio/caso de uso.
    """

    archivo = forms.FileField(label="Archivo Excel")

    EXTENSIONES_PERMITIDAS = {".xlsx", ".xls", ".ods", ".csv"}

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if not archivo:
            return archivo

        _, ext = os.path.splitext(archivo.name.lower())
        if ext not in self.EXTENSIONES_PERMITIDAS:
            raise forms.ValidationError(
                "Extensión no permitida. Use uno de: %s"
                % ", ".join(sorted(self.EXTENSIONES_PERMITIDAS))
            )
        return archivo
