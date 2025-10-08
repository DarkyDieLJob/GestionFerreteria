# Archivo de vistas del adaptador
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import FormView
from django.views import View
from django.core.files.storage import FileSystemStorage

# Estas vistas actúan como adaptadores en la arquitectura hexagonal.
# Delegan la lógica de negocio al repositorio y a los casos de uso del dominio,
# manteniendo a Django como capa de presentación.
from importaciones.adapters.repository import ExcelRepository
from importaciones.adapters.forms import ImportacionForm
from proveedores.models import Proveedor

# Nota: ImportacionForm se define en importaciones.adapters.forms y se integra aquí
# como form_class de ImportacionCreateView.


class ImportacionCreateView(FormView):
    """
    Vista para subir un archivo Excel para un proveedor específico.

    - template_name: plantilla del formulario.
    - form_class: formulario simple con FileField (ImportacionForm).
    - Al validar, almacena el archivo con FileSystemStorage y delega el
      procesamiento al ExcelRepository.
    - Finalmente redirige al listado de proveedores.

    Nota: Las consultas a Proveedor/ConfigImportacion se realizan sobre la
    base de datos por defecto a través del repositorio.
    """

    template_name = "importaciones/importacion_form.html"
    form_class = ImportacionForm

    def form_valid(self, form):
        proveedor_id = self.kwargs.get("proveedor_id")

        # Guardar el archivo con el storage por defecto (MEDIA_ROOT)
        archivo = form.cleaned_data["archivo"]
        storage = FileSystemStorage()
        nombre_archivo = storage.save(archivo.name, archivo)

        # Integración con repositorio: procesar el archivo utilizando la
        # política de base de datos 'negocio_db' definida en el repositorio/modelos.
        ExcelRepository().procesar_excel(proveedor_id, nombre_archivo)

        # Redirigir al listado de proveedores (namespace 'proveedores').
        return redirect(reverse("proveedores:proveedor_list"))


class ImportacionPreviewView(View):
    """
    Muestra una vista previa (primeras filas) del contenido del Excel
    previamente subido para un proveedor.

    - template_name: plantilla para renderizar la vista previa.
    - En GET, obtiene proveedor_id y nombre_archivo desde la URL y delega en el
      repositorio la lectura de las primeras filas.

    Las operaciones de lectura/consulta respetan 'negocio_db' según
    implementación del repositorio/modelos.
    """

    template_name = "importaciones/importacion_preview.html"

    def get(self, request, *args, **kwargs):
        proveedor_id = kwargs.get("proveedor_id")
        nombre_archivo = kwargs.get("nombre_archivo")

        # Obtener las primeras 20 filas para vista previa
        filas = ExcelRepository().vista_previa_excel(
            proveedor_id=proveedor_id,
            nombre_archivo=nombre_archivo,
            limite=20,
        )

        contexto = {
            "proveedor_id": proveedor_id,
            "nombre_archivo": nombre_archivo,
            "filas": filas,
        }
        return render(request, self.template_name, contexto)


class ImportacionesLandingView(View):
    """
    Landing para seleccionar un proveedor y comenzar el flujo de importación.
    - GET: muestra selector de proveedor.
    - POST: redirige a importacion_create con el proveedor elegido.
    """

    template_name = "importaciones/landing.html"

    def get(self, request, *args, **kwargs):
        proveedores = Proveedor.objects.all().order_by("nombre")
        return render(request, self.template_name, {"proveedores": proveedores})

    def post(self, request, *args, **kwargs):
        proveedor_id = request.POST.get("proveedor_id")
        if not proveedor_id:
            proveedores = Proveedor.objects.all().order_by("nombre")
            return render(
                request,
                self.template_name,
                {
                    "proveedores": proveedores,
                    "error": "Selecciona un proveedor para continuar.",
                },
            )
        return redirect(
            reverse("importaciones:importacion_create", kwargs={"proveedor_id": proveedor_id})
        )