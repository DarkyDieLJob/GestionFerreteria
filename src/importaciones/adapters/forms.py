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


class ConfigImportacionForm(forms.ModelForm):
    """ModelForm para crear/editar ConfigImportacion.

    Incluye todos los campos relevantes y fija proveedor como oculto
    para ser inyectado desde la vista o el formset.
    """

    class Meta:
        from django.apps import apps

        model = apps.get_model("importaciones", "ConfigImportacion")
        fields = [
            "proveedor",
            "nombre_config",
            "col_codigo",
            "col_descripcion",
            "col_precio",
            "col_cant",
            "col_iva",
            "col_cod_barras",
            "col_marca",
            "instructivo",
        ]
        widgets = {
            "proveedor": forms.HiddenInput(),
            "instructivo": forms.Textarea(attrs={"rows": 3}),
        }


class PreviewHojaForm(forms.Form):
    """Formulario para configurar la importación por hoja.

    Campos:
      - hoja: nombre de la hoja (oculto, informativo)
      - cargar: checkbox para indicar si se debe procesar
      - config_choice: selección entre "Nueva" o una ConfigImportacion existente
      - start_row: fila inicial (cero por defecto)
      - campos de nueva configuración (si se elige "Nueva"): nombre_config, col_*, instructivo
    """

    hoja = forms.CharField(widget=forms.HiddenInput())
    cargar = forms.BooleanField(required=False, initial=False, label="Cargar")
    config_choice = forms.ChoiceField(required=False, label="Configuración")
    start_row = forms.IntegerField(min_value=0, initial=0, label="Fila inicial")

    # Campos de la nueva configuración (solo requeridos si se elige "Nueva")
    proveedor = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    nombre_config = forms.CharField(required=False, label="Nombre de la configuración")
    col_codigo = forms.CharField(required=False, label="Columna código (A, B, ... o índice)")
    col_descripcion = forms.CharField(required=False, label="Columna descripción")
    col_precio = forms.CharField(required=False, label="Columna precio")
    col_cant = forms.CharField(required=False, label="Columna cantidad")
    col_iva = forms.CharField(required=False, label="Columna IVA")
    col_cod_barras = forms.CharField(required=False, label="Columna código de barras")
    col_marca = forms.CharField(required=False, label="Columna marca")
    instructivo = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Instructivo")

    def __init__(self, *args, **kwargs):
        # kwargs adicionales: proveedor para filtrar configs
        self.proveedor = kwargs.pop("proveedor", None)
        super().__init__(*args, **kwargs)

        # Cargar queryset de configuraciones si se pasó proveedor
        from django.apps import apps

        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        qs = ConfigImportacion.objects.none()
        if self.proveedor is not None:
            # Usar la misma base de datos del proveedor cuando aplique
            try:
                qs = ConfigImportacion.objects.using("negocio_db").filter(proveedor=self.proveedor).order_by(
                    "nombre_config", "id"
                )
            except Exception:
                qs = ConfigImportacion.objects.filter(proveedor=self.proveedor).order_by("nombre_config", "id")

        # Armar choices: opción "Nueva" + existentes
        choices = [("", "-- seleccionar --"), ("__new__", "Nueva configuración")]
        choices.extend([(str(o.pk), f"{o.nombre_config}") for o in qs])
        self.fields["config_choice"].choices = choices

        # Si no hay configuraciones, orientar al usuario
        if not qs.exists():
            self.fields["config_choice"].help_text = (
                "No hay configuraciones para el proveedor. Selecciona 'Nueva configuración' y completa los campos."
            )
        else:
            self.fields["config_choice"].help_text = (
                "Puedes seleccionar una existente o 'Nueva configuración' para definir otra."
            )

        # Propagar proveedor oculto en el formulario para creación de nueva config
        if self.proveedor is not None:
            self.fields["proveedor"].initial = getattr(self.proveedor, "pk", self.proveedor)

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("cargar"):
            # Si no se va a cargar, no forzar más validaciones
            return cleaned

        choice = cleaned.get("config_choice")
        # Si es nueva config, exigir nombre y mapeos mínimos
        if choice in ("", "__new__"):
            faltan = []
            if not cleaned.get("nombre_config"):
                faltan.append("nombre_config")
            if not cleaned.get("col_codigo"):
                faltan.append("col_codigo")
            if not cleaned.get("col_descripcion"):
                faltan.append("col_descripcion")
            if not cleaned.get("col_precio"):
                faltan.append("col_precio")
            if faltan:
                raise forms.ValidationError(
                    "Para crear una nueva configuración faltan: %s" % ", ".join(faltan)
                )
        else:
            # Debe ser un ID válido; la vista resolverá a instancia real
            try:
                int(choice)
            except (TypeError, ValueError):
                raise forms.ValidationError("Configuración seleccionada inválida.")
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
