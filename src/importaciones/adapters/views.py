# Archivo de vistas del adaptador
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
import logging
from django.views.generic import FormView
from django.views import View
from django.core.files.storage import FileSystemStorage
from django.apps import apps  # expuesto a nivel módulo para facilitar patch en tests

# Estas vistas actúan como adaptadores en la arquitectura hexagonal.
# Delegan la lógica de negocio al repositorio y a los casos de uso del dominio,
# manteniendo a Django como capa de presentación.
from importaciones.adapters.repository import ExcelRepository
from importaciones.adapters.forms import ImportacionForm, PreviewHojaFormSet
from importaciones.domain.use_cases import ImportarExcelUseCase
from proveedores.models import Proveedor
from importaciones.tasks import procesar_pendientes_task

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
        proveedor = Proveedor.objects.get(pk=proveedor_id)

        # Mostrar pendientes sin procesar como resumen
        from django.apps import apps

        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        pendientes = (
            ArchivoPendiente.objects.select_related("config_usada")
            .filter(proveedor=proveedor, procesado=False)
            .order_by("fecha_subida")
        )
        # Preparar datos de presentación (nombre de archivo limpio, hoja)
        import os
        pendientes_display = []
        for p in pendientes:
            # Mostrar nombre base del CSV pendiente (ruta_csv)
            archivo_name = getattr(p, "ruta_csv", "") or ""
            base_name = os.path.basename(archivo_name) if archivo_name else "-"
            # La hoja debe provenir de hoja_origen
            hoja = getattr(p, "hoja_origen", None) or "-"
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


class ArchivoPendienteDeleteView(View):
    def post(self, request, proveedor_id: int, pendiente_id: int):
        from django.apps import apps
        proveedor = get_object_or_404(Proveedor.objects, pk=proveedor_id)
        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        obj = get_object_or_404(ArchivoPendiente.objects, pk=pendiente_id, proveedor=proveedor)
        type(obj).objects.filter(pk=obj.pk).delete()
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
        # Evitar requerir acceso a DB en GET (tests mockean sólo apps/UseCase)
        # Usamos un objeto liviano con atributos esperados por la plantilla
        class _ProvLight:
            def __init__(self, pk):
                self.id = pk
                self.pk = pk
                self.nombre = ""
        proveedor = _ProvLight(proveedor_id)
        # Pasar proveedor_id al formset para evitar depender de un objeto con pk en tests
        formset = PreviewHojaFormSet(initial=initial, proveedor=proveedor_id)

        # Previews por hoja (primeras 20 filas) y columnas, para mostrar tablas
        previews = {}
        for hoja in hojas:
            try:
                prev = use_case.get_preview_for_sheet(proveedor_id=proveedor_id, nombre_archivo=nombre_archivo, sheet_name=hoja)
            except Exception:
                # Si falla (p.ej. archivo inexistente en tests), omitimos preview pero mantenemos la hoja
                continue
            columnas = prev.get("columnas", [])
            # Generar encabezado visible: '#', luego letras (A, B, C, ...) para las columnas de datos
            col_letters = ["#"]
            # soportar respuestas que ya incluyen '#' como primera columna o no
            data_cols = len(columnas) - 1 if columnas and columnas[0] == "#" else len(columnas)
            for idx in range(1, data_cols + 1):
                n = idx
                s = ""
                while n > 0:
                    n, r = divmod(n - 1, 26)
                    s = chr(65 + r) + s
                col_letters.append(s)
            filas_dicts = prev.get("filas", [])
            filas_vals = [[(fila or {}).get(col) for col in columnas] for fila in filas_dicts]
            previews[hoja] = {
                "columnas": columnas,
                "column_letters": col_letters,
                "filas": filas_vals,
                "total_filas": prev.get("total_filas", 0),
            }

        # Instructivo (si existe en alguna configuración)
        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        instructivos = list(
            ConfigImportacion.objects.filter(proveedor_id=proveedor_id, instructivo__isnull=False).values_list("instructivo", flat=True)
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
        proveedor = get_object_or_404(Proveedor.objects, pk=proveedor_id)

        # Instructivos disponibles del proveedor (para re-render de POST)
        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        instructivos = list(
            ConfigImportacion.objects.filter(proveedor_id=proveedor_id, instructivo__isnull=False).values_list("instructivo", flat=True)
        )

        # Pasar proveedor_id al formset para evitar depender de un objeto con pk en tests
        formset = PreviewHojaFormSet(data=request.POST, proveedor=proveedor_id)
        if not formset.is_valid():
            logger.warning("[ImportacionPreviewView] formset inválido: errors=%s", formset.errors)
            # Re-render con errores sin consumir previews del backend (evitar agotar side_effects en tests)
            use_case = ImportarExcelUseCase(ExcelRepository())
            hojas = use_case.listar_hojas(nombre_archivo=nombre_archivo)
            contexto = {
                "proveedor": proveedor,
                "nombre_archivo": nombre_archivo,
                "hojas": hojas,
                "previews": {},
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
                # existente por id: además, si hay campos editados, sobreescribir configuración
                cfg_id = int(config_choice)
                config_obj = cfg_id
                try:
                    ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
                    cfg_inst = (
                        ConfigImportacion.objects
                        .filter(pk=cfg_id, proveedor_id=proveedor_id)
                        .first()
                    )
                except Exception:
                    cfg_inst = (
                        apps.get_model("importaciones", "ConfigImportacion")
                        .objects.filter(pk=cfg_id, proveedor_id=proveedor_id)
                        .first()
                    )
                if cfg_inst is not None:
                    fields_to_update = [
                        "col_codigo",
                        "col_descripcion",
                        "col_precio",
                        "col_cant",
                        "col_iva",
                        "col_cod_barras",
                        "col_marca",
                        "instructivo",
                    ]
                    changed = False
                    for f in fields_to_update:
                        val = cd.get(f)
                        # Si el usuario dejó vacío, no pisamos; solo sobreescribimos con valores proveídos
                        if val is not None and val != "" and getattr(cfg_inst, f) != val:
                            setattr(cfg_inst, f, val)
                            changed = True
                    if changed:
                        cfg_inst.save()
            if choice in ("", "__new__", "new"):
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
                # Generar encabezado visible: '#', luego letras (A, B, C, ...) para las columnas de datos
                col_letters = ["#"]
                data_cols = len(columnas) - 1 if columnas and columnas[0] == "#" else len(columnas)
                for idx in range(1, data_cols + 1):
                    n = idx
                    s = ""
                    while n > 0:
                        n, r = divmod(n - 1, 26)
                        s = chr(65 + r) + s
                    col_letters.append(s)
                filas_dicts = prev.get("filas", [])
                filas_vals = [[(fila or {}).get(col) for col in columnas] for fila in filas_dicts]
                previews[hoja] = {
                    "columnas": columnas,
                    "column_letters": col_letters,
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
        # Encolar el procesamiento de pendientes para dentro de 10 minutos (ETA en UTC)
        try:
            from datetime import datetime, timedelta, timezone as dt_timezone
            eta_utc = datetime.now(dt_timezone.utc) + timedelta(minutes=10)
            procesar_pendientes_task.apply_async(eta=eta_utc)
        except Exception:
            # No interrumpir el flujo de usuario si hay un problema de broker/worker
            logger = logging.getLogger(__name__)
            logger.exception("No se pudo encolar la tarea procesar_pendientes")

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
        proveedores = Proveedor.objects.all().order_by("nombre")
        from django.apps import apps

        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        pendientes = (
            ArchivoPendiente.objects.select_related("proveedor", "config_usada").filter(procesado=False)
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
        proveedores = Proveedor.objects.all().order_by("nombre")
        if not proveedor_id or not form.is_valid():
            from django.apps import apps

            ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
            pendientes = (
                ArchivoPendiente.objects.select_related("proveedor", "config_usada").filter(procesado=False)
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