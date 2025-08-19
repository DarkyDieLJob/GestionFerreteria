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


class PreviewHojaForm(forms.Form):
    """Formulario para configurar la importación por hoja.

    Campos:
      - hoja: nombre de la hoja (oculto, informativo)
      - cargar: checkbox para indicar si se debe procesar
      - config: selección de ConfigImportacion (si existen)
      - start_row: fila inicial (cero por defecto)
      - overrides de columnas: col_codigo, col_descripcion, col_precio (si no hay config)
    """

    hoja = forms.CharField(widget=forms.HiddenInput())
    cargar = forms.BooleanField(required=False, initial=False, label="Cargar")
    config = forms.ModelChoiceField(
        queryset=None, required=False, empty_label="-- seleccionar --", label="Configuración"
    )
    start_row = forms.IntegerField(min_value=0, initial=0, label="Fila inicial")

    # Overrides cuando no hay configuración elegida
    col_codigo = forms.CharField(required=False, label="Columna código (A, B, ... o índice)")
    col_descripcion = forms.CharField(required=False, label="Columna descripción")
    col_precio = forms.CharField(required=False, label="Columna precio")

    def __init__(self, *args, **kwargs):
        # kwargs adicionales: proveedor para filtrar configs
        self.proveedor = kwargs.pop("proveedor", None)
        super().__init__(*args, **kwargs)

        # Cargar queryset de configuraciones si se pasó proveedor
        from django.apps import apps

        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        qs = ConfigImportacion.objects.none()
        if self.proveedor is not None:
            qs = ConfigImportacion.objects.filter(proveedor=self.proveedor).order_by("nombre_config", "id")
        self.fields["config"].queryset = qs

        # Si no hay configuraciones, mostrar ayudas para overrides
        if not qs.exists():
            self.fields["config"].help_text = "No hay configuraciones para el proveedor. Complete las columnas manualmente."
        else:
            self.fields["config"].help_text = "Opcional: si se selecciona, no son necesarios los overrides de columnas."

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("cargar"):
            # Si no se va a cargar, no forzar más validaciones
            return cleaned

        config = cleaned.get("config")
        # Si no hay configuración, requerir overrides mínimos
        if not config:
            faltan = []
            if not cleaned.get("col_codigo"):
                faltan.append("col_codigo")
            if not cleaned.get("col_descripcion"):
                faltan.append("col_descripcion")
            if not cleaned.get("col_precio"):
                faltan.append("col_precio")
            if faltan:
                raise forms.ValidationError(
                    "Faltan columnas obligatorias al no seleccionar una configuración: %s"
                    % ", ".join(faltan)
                )
        return cleaned


class BasePreviewFormSet(forms.formsets.BaseFormSet):
    """FormSet para múltiples hojas. Inyecta el proveedor a cada formulario."""

    def __init__(self, *args, **kwargs):
        self.proveedor = kwargs.pop("proveedor", None)
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["proveedor"] = self.proveedor
        return kwargs


PreviewHojaFormSet = forms.formset_factory(
    PreviewHojaForm,
    formset=BasePreviewFormSet,
    extra=0,
)
