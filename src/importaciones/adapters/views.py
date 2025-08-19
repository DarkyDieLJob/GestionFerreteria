# Archivo de vistas del adaptador
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
import logging
from django.views.generic import FormView
from django.views import View
from django.core.files.storage import FileSystemStorage

# Estas vistas actúan como adaptadores en la arquitectura hexagonal.
# Delegan la lógica de negocio al repositorio y a los casos de uso del dominio,
# manteniendo a Django como capa de presentación.
from importaciones.adapters.repository import ExcelRepository
from importaciones.adapters.forms import ImportacionForm, PreviewHojaFormSet
from importaciones.domain.use_cases import ImportarExcelUseCase
from proveedores.models import Proveedor

# Nota: ImportacionForm se define en importaciones.adapters.forms y se integra aquí
# como form_class de ImportacionCreateView.


class ImportacionCreateView(View):
    """
    Vista de confirmación del nuevo flujo.
    - GET: muestra resumen luego de agendar pendientes (CSV generados por hoja).
    """

    template_name = "importaciones/importacion_confirm.html"

    def get(self, request, *args, **kwargs):
        proveedor_id = kwargs.get("proveedor_id")
        proveedor = Proveedor.objects.using("negocio_db").get(pk=proveedor_id)

        # Mostrar pendientes sin procesar como resumen
        from django.apps import apps

        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        pendientes = (
            ArchivoPendiente.objects.using("negocio_db").select_related("config_usada")
            .filter(proveedor=proveedor, procesado=False)
            .order_by("fecha_subida")
        )
        # Preparar datos de presentación (nombre de archivo limpio, hoja)
        import os
        pendientes_display = []
        for p in pendientes:
            try:
                archivo_name = getattr(p.archivo_csv, "name", None) or getattr(p, "archivo_csv", None) or ""
            except Exception:
                archivo_name = str(p.archivo_csv) if hasattr(p, "archivo_csv") else ""
            base_name = os.path.basename(archivo_name) if archivo_name else "-"
            hoja = getattr(p, "hoja", None) or "-"
            pendientes_display.append({
                "obj": p,
                "archivo_base": base_name,
                "hoja": hoja,
            })
        contexto = {
            "proveedor": proveedor,
            "pendientes": pendientes_display,
        }
        return render(request, self.template_name, contexto)


class ArchivoPendienteEditView(View):
    template_name = "importaciones/pendiente_edit.html"

    def get(self, request, proveedor_id: int, pendiente_id: int):
        from django.apps import apps
        proveedor = get_object_or_404(Proveedor.objects.using("negocio_db"), pk=proveedor_id)
        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        obj = get_object_or_404(ArchivoPendiente.objects.using("negocio_db").select_related("config_usada"), pk=pendiente_id, proveedor=proveedor)
        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        configs = list(ConfigImportacion.objects.using("negocio_db").filter(proveedor=proveedor).order_by("nombre_config"))
        contexto = {
            "proveedor": proveedor,
            "obj": obj,
            "configs": configs,
        }
        return render(request, self.template_name, contexto)

    def post(self, request, proveedor_id: int, pendiente_id: int):
        from django.apps import apps
        proveedor = get_object_or_404(Proveedor.objects.using("negocio_db"), pk=proveedor_id)
        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        obj = get_object_or_404(ArchivoPendiente.objects.using("negocio_db"), pk=pendiente_id, proveedor=proveedor)
        # Campos editables mínimos: hoja y config_usada
        hoja = request.POST.get("hoja")
        config_id = request.POST.get("config_usada")
        updates = {}
        if hoja is not None:
            updates["hoja"] = hoja
        if config_id:
            ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
            cfg = ConfigImportacion.objects.using("negocio_db").filter(pk=config_id, proveedor=proveedor).first()
            if cfg:
                updates["config_usada_id"] = cfg.pk
        if updates:
            type(obj).objects.using("negocio_db").filter(pk=obj.pk).update(**updates)
        return redirect(reverse("importaciones:importacion_create", kwargs={"proveedor_id": proveedor_id}))


class ArchivoPendienteDeleteView(View):
    def post(self, request, proveedor_id: int, pendiente_id: int):
        from django.apps import apps
        proveedor = get_object_or_404(Proveedor.objects.using("negocio_db"), pk=proveedor_id)
        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        obj = get_object_or_404(ArchivoPendiente.objects.using("negocio_db"), pk=pendiente_id, proveedor=proveedor)
        type(obj).objects.using("negocio_db").filter(pk=obj.pk).delete()
        return redirect(reverse("importaciones:importacion_create", kwargs={"proveedor_id": proveedor_id}))


class ImportacionPreviewView(View):
    """
    Vista de previsualización por hoja del Excel subido.
    - GET: lista hojas y arma un formset para elegir configuración por hoja y start_row.
           Incluye instructivo si existe en ConfigImportacion.
    - POST: procesa formset y genera CSVs por hoja mediante el caso de uso; redirige a confirmación.
    """

    template_name = "importaciones/importacion_preview.html"

    def get(self, request, *args, **kwargs):
        proveedor_id = kwargs.get("proveedor_id")
        nombre_archivo = kwargs.get("nombre_archivo")

        use_case = ImportarExcelUseCase(ExcelRepository())
        hojas = use_case.listar_hojas(nombre_archivo=nombre_archivo)

        # Inicializar formset una fila por hoja
        initial = [{"hoja": h, "start_row": 0, "cargar": False} for h in hojas]
        proveedor = Proveedor.objects.using("negocio_db").get(pk=proveedor_id)
        formset = PreviewHojaFormSet(initial=initial, proveedor=proveedor)

        # Previews por hoja (primeras 20 filas) y columnas, para mostrar tablas
        previews = {}
        for hoja in hojas:
            prev = use_case.get_preview_for_sheet(proveedor_id=proveedor_id, nombre_archivo=nombre_archivo, sheet_name=hoja)
            columnas = prev.get("columnas", [])
            filas_dicts = prev.get("filas", [])
            filas_vals = [[(fila or {}).get(col) for col in columnas] for fila in filas_dicts]
            previews[hoja] = {
                "columnas": columnas,
                "filas": filas_vals,
                "total_filas": prev.get("total_filas", 0),
            }

        # Instructivo (si existe en alguna configuración)
        from django.apps import apps

        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        instructivos = list(
            ConfigImportacion.objects.using("negocio_db").filter(proveedor=proveedor, instructivo__isnull=False).values_list("instructivo", flat=True)
        )

        contexto = {
            "proveedor": proveedor,
            "nombre_archivo": nombre_archivo,
            "hojas": hojas,
            "previews": previews,
            "formset": formset,
            "instructivos": instructivos,
        }
        return render(request, self.template_name, contexto)

    def post(self, request, proveedor_id: int, nombre_archivo: str):
        logger = logging.getLogger(__name__)
        logger.info(
            "[ImportacionPreviewView] POST recibido proveedor_id=%s nombre_archivo=%s",
            proveedor_id,
            nombre_archivo,
        )
        proveedor = get_object_or_404(Proveedor.objects.using("negocio_db"), pk=proveedor_id)

        # Instructivos disponibles del proveedor (para re-render de POST)
        from django.apps import apps
        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        instructivos = list(
            ConfigImportacion.objects.using("negocio_db").filter(proveedor=proveedor, instructivo__isnull=False).values_list("instructivo", flat=True)
        )

        formset = PreviewHojaFormSet(data=request.POST, proveedor=proveedor)
        if not formset.is_valid():
            logger.warning("[ImportacionPreviewView] formset inválido: errors=%s", formset.errors)
            # Re-render con errores y previews
            use_case = ImportarExcelUseCase(ExcelRepository())
            hojas = use_case.listar_hojas(nombre_archivo=nombre_archivo)
            previews = {}
            for hoja in hojas:
                prev = use_case.get_preview_for_sheet(proveedor_id=proveedor_id, nombre_archivo=nombre_archivo, sheet_name=hoja)
                columnas = prev.get("columnas", [])
                filas_dicts = prev.get("filas", [])
                filas_vals = [[(fila or {}).get(col) for col in columnas] for fila in filas_dicts]
                previews[hoja] = {
                    "columnas": columnas,
                    "filas": filas_vals,
                    "total_filas": prev.get("total_filas", 0),
                }
            contexto = {
                "proveedor": proveedor,
                "nombre_archivo": nombre_archivo,
                "hojas": hojas,
                "previews": previews,
                "formset": formset,
                "instructivos": instructivos,
            }
            return render(request, self.template_name, contexto)

        # Procesar cada formulario del formset
        selecciones = {}
        for form in formset:
            cd = form.cleaned_data
            if not cd.get("cargar"):
                logger.debug("[ImportacionPreviewView] hoja=%s no marcada para cargar", cd.get("hoja"))
                continue
            hoja = cd.get("hoja")
            start_row = cd.get("start_row") or 0
            choice = cd.get("config_choice")
            logger.debug(
                "[ImportacionPreviewView] hoja=%s cargar=True start_row=%s choice=%s",
                hoja,
                start_row,
                choice,
            )
            # Configuración: existente o nueva
            config_obj = None
            config_choice = cd.get("config_choice")
            if config_choice and str(config_choice).isdigit():
                # existente por id
                config_obj = int(config_choice)
            if choice in ("", "__new__"):
                # Crear o asegurar configuración
                repo = ExcelRepository()
                data_cfg = {
                    "proveedor_id": proveedor_id,
                    "nombre_config": cd.get("nombre_config"),
                    "col_codigo": cd.get("col_codigo"),
                    "col_descripcion": cd.get("col_descripcion"),
                    "col_precio": cd.get("col_precio"),
                    "col_cant": cd.get("col_cant"),
                    "col_iva": cd.get("col_iva"),
                    "col_cod_barras": cd.get("col_cod_barras"),
                    "col_marca": cd.get("col_marca"),
                    "instructivo": cd.get("instructivo"),
                }
                logger.info("[ImportacionPreviewView] creando/asegurando config nueva para hoja=%s datos=%s", hoja, data_cfg)
                created_cfg = repo.ensure_config(proveedor_id=proveedor_id, data=data_cfg)
                config_obj = created_cfg.pk
            else:
                logger.debug("[ImportacionPreviewView] usando config existente id=%s para hoja=%s", choice, hoja)
                
            if config_obj is not None:
                selecciones[hoja] = {"config_id": int(config_obj), "start_row": start_row}

        if not selecciones:
            # Nada seleccionado
            logger.info("[ImportacionPreviewView] no hay hojas seleccionadas; se re-renderiza la vista")
            use_case = ImportarExcelUseCase(ExcelRepository())
            hojas = use_case.listar_hojas(nombre_archivo=nombre_archivo)
            previews = {}
            for hoja in hojas:
                prev = use_case.get_preview_for_sheet(proveedor_id=proveedor_id, nombre_archivo=nombre_archivo, sheet_name=hoja)
                columnas = prev.get("columnas", [])
                filas_dicts = prev.get("filas", [])
                filas_vals = [[(fila or {}).get(col) for col in columnas] for fila in filas_dicts]
                previews[hoja] = {
                    "columnas": columnas,
                    "filas": filas_vals,
                    "total_filas": prev.get("total_filas", 0),
                }
            contexto = {
                "proveedor": proveedor,
                "nombre_archivo": nombre_archivo,
                "hojas": hojas,
                "previews": previews,
                "formset": formset,
                "warning": "No seleccionaste ninguna hoja para cargar.",
                "instructivos": instructivos,
            }
            return render(request, self.template_name, contexto)

        # Generar CSVs y encolar pendientes
        logger.info("[ImportacionPreviewView] generando CSVs selecciones=%s", selecciones)
        use_case = ImportarExcelUseCase(ExcelRepository())
        use_case.generar_csvs_por_hoja(proveedor_id=proveedor_id, nombre_archivo=nombre_archivo, selecciones=selecciones)

        # Redirigir a vista de confirmación existente en urls (importacion_create)
        logger.info("[ImportacionPreviewView] redireccionando a importacion_create proveedor_id=%s", proveedor_id)
        return redirect(reverse("importaciones:importacion_create", kwargs={"proveedor_id": proveedor_id}))


class ImportacionesLandingView(View):
    """
    Landing del flujo de importación.
    - GET: lista archivos pendientes y muestra selector de proveedor + upload.
    - POST: recibe archivo + proveedor, guarda el archivo y redirige a preview.
    """

    template_name = "importaciones/landing.html"

    def get(self, request, *args, **kwargs):
        proveedores = Proveedor.objects.using("negocio_db").all().order_by("nombre")
        from django.apps import apps

        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        pendientes = (
            ArchivoPendiente.objects.using("negocio_db").select_related("proveedor", "config_usada").filter(procesado=False)
            .order_by("fecha_subida")
        )
        form = ImportacionForm()
        contexto = {
            "proveedores": proveedores,
            "pendientes": pendientes,
            "form": form,
        }
        return render(request, self.template_name, contexto)

    def post(self, request, *args, **kwargs):
        proveedor_id = request.POST.get("proveedor_id")
        form = ImportacionForm(request.POST, request.FILES)
        proveedores = Proveedor.objects.using("negocio_db").all().order_by("nombre")
        if not proveedor_id or not form.is_valid():
            from django.apps import apps

            ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
            pendientes = (
                ArchivoPendiente.objects.using("negocio_db").select_related("proveedor", "config_usada").filter(procesado=False)
                .order_by("fecha_subida")
            )
            contexto = {
                "proveedores": proveedores,
                "pendientes": pendientes,
                "form": form,
                "error": "Selecciona proveedor y archivo válido.",
            }
            return render(request, self.template_name, contexto)

        # Guardar el archivo y redirigir a vista previa
        archivo = form.cleaned_data["archivo"]
        storage = FileSystemStorage()
        nombre_archivo = storage.save(archivo.name, archivo)

        return redirect(
            reverse(
                "importaciones:importacion_preview",
                kwargs={"proveedor_id": int(proveedor_id), "nombre_archivo": nombre_archivo},
            )
        )


class ConfigImportacionDetailView(View):
    """Devuelve en JSON los datos de una ConfigImportacion del proveedor dado.

    GET params:
      - id: ID de la configuración
    """

    def get(self, request, proveedor_id: int):
        config_id = request.GET.get("id")
        if not config_id:
            return HttpResponseBadRequest("Falta parámetro id")
        try:
            config_id_int = int(config_id)
        except ValueError:
            return HttpResponseBadRequest("Parámetro id inválido")

        from django.apps import apps

        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        try:
            obj = (
                ConfigImportacion.objects.using("negocio_db")
                .filter(proveedor_id=proveedor_id, id=config_id_int)
                .only(
                    "id",
                    "nombre_config",
                    "col_codigo",
                    "col_descripcion",
                    "col_precio",
                    "col_cant",
                    "col_iva",
                    "col_cod_barras",
                    "col_marca",
                    "instructivo",
                )
                .first()
            )
        except Exception:
            obj = (
                ConfigImportacion.objects
                .filter(proveedor_id=proveedor_id, id=config_id_int)
                .only(
                    "id",
                    "nombre_config",
                    "col_codigo",
                    "col_descripcion",
                    "col_precio",
                    "col_cant",
                    "col_iva",
                    "col_cod_barras",
                    "col_marca",
                    "instructivo",
                )
                .first()
            )

        if not obj:
            return HttpResponseBadRequest("Configuración no encontrada para este proveedor")

        data = {
            "id": obj.id,
            "nombre_config": obj.nombre_config,
            "col_codigo": obj.col_codigo,
            "col_descripcion": obj.col_descripcion,
            "col_precio": obj.col_precio,
            "col_cant": obj.col_cant,
            "col_iva": obj.col_iva,
            "col_cod_barras": obj.col_cod_barras,
            "col_marca": obj.col_marca,
            "instructivo": obj.instructivo,
        }
        return JsonResponse(data)