# Archivo del repositorio del adaptador
"""
Repositorio del adaptador para el caso de uso de importación de Excel.

Implementa el puerto `ImportarExcelPort` del dominio de importaciones
usando Django ORM, pandas y almacenamiento de archivos del sistema.

Todas las lecturas/escrituras de base de datos se realizan contra
la base de datos por defecto ("default").
"""

import os
import tempfile
from typing import Any, Dict, List, Tuple, Optional

import pandas as pd
from django.apps import apps
from django.core.files.storage import FileSystemStorage
from django.db import transaction
import logging

from ..domain.use_cases import ImportarExcelPort
from ..services.conversion import convertir_a_csv

logger = logging.getLogger("importaciones.repository")

class ExcelRepository(ImportarExcelPort):
    """
    Adaptador que procesa archivos Excel para generar/actualizar registros
    relacionados con listas de precios y artículos sin revisar.
    """

    def __init__(self) -> None:
        # Permite inyectar dependencias en el futuro si fuera necesario.
        self.storage = FileSystemStorage()

    def _load_models(self):
        Proveedor = apps.get_model("proveedores", "Proveedor")
        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        PrecioDeLista = apps.get_model("precios", "PrecioDeLista")
        ArticuloSinRevisar = apps.get_model("articulos", "ArticuloSinRevisar")
        Descuento = apps.get_model("precios", "Descuento")
        return Proveedor, ConfigImportacion, ArchivoPendiente, PrecioDeLista, ArticuloSinRevisar, Descuento

    def vista_previa_excel(self, proveedor_id: Any, nombre_archivo: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Lee el archivo y devuelve preview (primeras 20 filas) de una hoja específica si
        `sheet_name` está definido. También devuelve las columnas.
        No realiza escrituras en base de datos.

        Soporta .xlsx/.xls/.ods mediante pandas y .csv por ruta directa.
        """
        file_path = self.storage.path(nombre_archivo)
        _, ext = os.path.splitext(nombre_archivo.lower())

        if ext == ".csv":
            df = pd.read_csv(file_path)
            hoja = None
        else:
            # Sniff de contenido para definir mejor el engine y aplicar múltiples intentos
            def _sniff_excel_format(path: str) -> Optional[str]:
                try:
                    with open(path, "rb") as f:
                        header = f.read(8)
                    if header.startswith(b"PK"):
                        return "xlsx_like"
                    if header.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"):
                        return "xls_like"
                except Exception:
                    pass
                return None

            sniff = _sniff_excel_format(file_path)
            candidates: List[Optional[str]] = []
            if sniff == "xlsx_like":
                candidates = ["openpyxl", "xlrd", None]
            elif sniff == "xls_like":
                candidates = ["xlrd", "openpyxl", None]
            else:
                if ext == ".xlsx":
                    candidates = ["openpyxl", "xlrd", None]
                elif ext == ".xls":
                    candidates = ["xlrd", "openpyxl", None]
                elif ext == ".ods":
                    candidates = ["odf", None]
                else:
                    candidates = [None, "openpyxl", "xlrd"]

            last_exc: Optional[Exception] = None
            for engine in candidates:
                try:
                    if sheet_name is not None:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine) if engine else pd.read_excel(file_path, sheet_name=sheet_name)
                        hoja = sheet_name
                    else:
                        df = pd.read_excel(file_path, engine=engine) if engine else pd.read_excel(file_path)
                        hoja = getattr(getattr(df, "name", None), "name", None) or None
                    last_exc = None
                    break
                except Exception as exc:
                    # Fallback adicional: si es .xls-like y falla xlrd, intentar convertir a xlsx y leer con openpyxl
                    if engine == "xlrd":
                        try:
                            from xls2xlsx import XLS2XLSX  # type: ignore
                            fd, tmp_xlsx = tempfile.mkstemp(suffix=".xlsx")
                            os.close(fd)
                            XLS2XLSX(file_path).to_xlsx(tmp_xlsx)
                            if sheet_name is not None:
                                df = pd.read_excel(tmp_xlsx, sheet_name=sheet_name, engine="openpyxl")
                                hoja = sheet_name
                            else:
                                df = pd.read_excel(tmp_xlsx, engine="openpyxl")
                                hoja = getattr(getattr(df, "name", None), "name", None) or None
                            last_exc = None
                            # limpieza best-effort
                            try:
                                os.remove(tmp_xlsx)
                            except Exception:
                                pass
                            break
                        except Exception:
                            last_exc = exc
                            continue
                    else:
                        last_exc = exc
                        continue
            if last_exc is not None:
                raise last_exc

        # Construir preview con índice visible (#) sin desplazar las columnas reales.
        # Las columnas se muestran como letras excel en minúscula: a, b, c, ...
        def _letters(n: int) -> List[str]:
            res: List[str] = []
            for i in range(n):
                s = ""
                x = i
                while True:
                    s = chr(ord('a') + (x % 26)) + s
                    x = x // 26 - 1
                    if x < 0:
                        break
                res.append(s)
            return res

        df_preview = df.head(20).fillna("")
        cols = _letters(df_preview.shape[1])

        def _is_header_like(r) -> bool:
            """Detecta filas de datos que son en realidad una repetición de encabezados (a,b,c,...)."""
            try:
                total = len(cols)
                # Coincidencias exactas (case-insensitive, trim) en las primeras columnas
                matches = 0
                for j in range(total):
                    val = str(r.iloc[j]).strip().lower()
                    if val == cols[j]:
                        matches += 1
                    elif val == "":
                        # permitir celdas vacías al final
                        continue
                    else:
                        # si aparece un valor no-vacío distinto, no es encabezado
                        return False
                # Consideramos encabezado si al menos 2-3 primeras columnas coinciden
                return matches >= min(3, total)
            except Exception:
                return False

        # Construimos filas como dict ordenado: primero '#', luego columnas por letras
        preview_rows: List[Dict[str, Any]] = []
        for idx, (_, row) in enumerate(df_preview.iterrows(), start=0):
            if _is_header_like(row):
                # Omitir filas que dupliquen encabezados para evitar doble header visual
                continue
            item: Dict[str, Any] = {"#": idx}
            for j, label in enumerate(cols):
                try:
                    item[label] = row.iloc[j]
                except Exception:
                    item[label] = ""
            preview_rows.append(item)

        return {
            "proveedor_id": proveedor_id,
            "archivo": nombre_archivo,
            "sheet_name": hoja,
            "columnas": ["#"] + cols,
            "filas": preview_rows,
            "total_filas": int(len(df)),
        }

    def listar_hojas_excel(self, nombre_archivo: str) -> List[str]:
        """Devuelve la lista de hojas disponibles en el Excel subido."""
        file_path = self.storage.path(nombre_archivo)
        _, ext = os.path.splitext(nombre_archivo.lower())

        def _sniff_excel_format(path: str) -> Optional[str]:
            try:
                with open(path, "rb") as f:
                    header = f.read(8)
                if header.startswith(b"PK"):
                    return "xlsx_like"
                if header.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"):
                    return "xls_like"
            except Exception:
                pass
            return None

        sniff = _sniff_excel_format(file_path)
        candidates: List[Optional[str]] = []
        if sniff == "xlsx_like":
            candidates = ["openpyxl", "xlrd", None]
        elif sniff == "xls_like":
            candidates = ["xlrd", "openpyxl", None]
        else:
            if ext == ".xlsx":
                candidates = ["openpyxl", "xlrd", None]
            elif ext == ".xls":
                candidates = ["xlrd", "openpyxl", None]
            elif ext == ".ods":
                candidates = ["odf", None]
            else:
                candidates = [None, "openpyxl", "xlrd"]

        last_exc: Optional[Exception] = None
        for engine in candidates:
            try:
                xls = pd.ExcelFile(file_path, engine=engine) if engine else pd.ExcelFile(file_path)
                return list(xls.sheet_names)
            except Exception as exc:
                # Fallback adicional: si xlrd falla, convertir a xlsx y reintentar con openpyxl
                if engine == "xlrd":
                    try:
                        from xls2xlsx import XLS2XLSX  # type: ignore
                        fd, tmp_xlsx = tempfile.mkstemp(suffix=".xlsx")
                        os.close(fd)
                        XLS2XLSX(file_path).to_xlsx(tmp_xlsx)
                        xls = pd.ExcelFile(tmp_xlsx, engine="openpyxl")
                        sheets = list(xls.sheet_names)
                        try:
                            os.remove(tmp_xlsx)
                        except Exception:
                            pass
                        return sheets
                    except Exception:
                        last_exc = exc
                        continue
                else:
                    last_exc = exc
                    continue
        raise RuntimeError(f"No se pudo abrir el archivo {nombre_archivo}") from last_exc

    def get_configs_for_proveedor(self, proveedor_id: Any) -> List[Dict[str, Any]]:
        """
        Obtiene las configuraciones disponibles para un proveedor, como lista de dicts
        apta para poblar choices del formulario o inicializar datos en la vista.
        Accede a la BD de negocio (negocio_db).
        """
        Proveedor, ConfigImportacion, *_ = self._load_models()
        proveedor = Proveedor.objects.get(pk=proveedor_id)
        configs = (
            ConfigImportacion.objects
            .filter(proveedor=proveedor)
            .order_by("nombre_config", "id")
        )
        salida: List[Dict[str, Any]] = []
        for c in configs:
            salida.append(
                {
                    "id": c.pk,
                    "nombre_config": c.nombre_config,
                    "col_codigo": c.col_codigo,
                    "col_descripcion": c.col_descripcion,
                    "col_precio": c.col_precio,
                    "col_cant": c.col_cant,
                    "col_iva": c.col_iva,
                    "col_cod_barras": c.col_cod_barras,
                    "col_marca": c.col_marca,
                    "instructivo": c.instructivo,
                }
            )
        return salida

    def ensure_config(self, proveedor_id: Any, data: Dict[str, Any]):
        """
        Crea (o devuelve existente) una ConfigImportacion para el proveedor según
        nombre_config y mapeos. Usa transacción atómica en negocio_db.
        """
        Proveedor, ConfigImportacion, *_ = self._load_models()
        proveedor = Proveedor.objects.get(pk=proveedor_id)
        nombre = data.get("nombre_config") or "default"
        defaults = {
            "col_codigo": data.get("col_codigo"),
            "col_descripcion": data.get("col_descripcion"),
            "col_precio": data.get("col_precio"),
            "col_cant": data.get("col_cant"),
            "col_iva": data.get("col_iva"),
            "col_cod_barras": data.get("col_cod_barras"),
            "col_marca": data.get("col_marca"),
            "instructivo": data.get("instructivo") or "",
        }
        with transaction.atomic():
            obj, created = ConfigImportacion.objects.get_or_create(
                proveedor=proveedor,
                nombre_config=nombre,
                defaults=defaults,
            )
            if not created:
                # Actualizar campos si cambiaron (edición en vista previa)
                changed = False
                for k, v in defaults.items():
                    if getattr(obj, k) != v and v is not None:
                        setattr(obj, k, v)
                        changed = True
                if changed:
                    obj.save()
        return obj

    def generar_csvs_por_hoja(
        self,
        proveedor_id: Any,
        nombre_archivo: str,
        selecciones: Dict[str, Dict[str, int]],
    ) -> List[Tuple[str, str]]:
        """
        Genera CSVs por hoja seleccionada y crea entradas en ArchivoPendiente.

        selecciones: dict de nombre_hoja -> { 'config_id': int, 'start_row': int }

        Retorna lista de tuplas (hoja, ruta_csv).
        """
        Proveedor, ConfigImportacion, ArchivoPendiente, *_ = self._load_models()

        proveedor = Proveedor.objects.get(pk=proveedor_id)

        file_path = self.storage.path(nombre_archivo)
        # Validar existencia de hojas (tolerando mayúsculas/minúsculas y espacios)
        _, ext = os.path.splitext(nombre_archivo.lower())

        def _sniff_excel_format(path: str) -> Optional[str]:
            try:
                with open(path, "rb") as f:
                    header = f.read(8)
                if header.startswith(b"PK"):
                    return "xlsx_like"
                if header.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"):
                    return "xls_like"
            except Exception:
                pass
            return None

        sniff = _sniff_excel_format(file_path)
        candidates: List[Optional[str]] = []
        if sniff == "xlsx_like":
            candidates = ["openpyxl", "xlrd", None]
        elif sniff == "xls_like":
            candidates = ["xlrd", "openpyxl", None]
        else:
            if ext == ".xlsx":
                candidates = ["openpyxl", "xlrd", None]
            elif ext == ".xls":
                candidates = ["xlrd", "openpyxl", None]
            elif ext == ".ods":
                candidates = ["odf", None]
            else:
                candidates = [None, "openpyxl", "xlrd"]

        disponibles_lista: List[str] = []
        last_exc: Optional[Exception] = None
        for engine in candidates:
            try:
                xls = pd.ExcelFile(file_path, engine=engine) if engine else pd.ExcelFile(file_path)
                disponibles_lista = list(xls.sheet_names)
                last_exc = None
                break
            except Exception as exc:
                # Fallback adicional: si xlrd falla, convertir a xlsx y reintentar con openpyxl
                if engine == "xlrd":
                    try:
                        from xls2xlsx import XLS2XLSX  # type: ignore
                        fd, tmp_xlsx = tempfile.mkstemp(suffix=".xlsx")
                        os.close(fd)
                        XLS2XLSX(file_path).to_xlsx(tmp_xlsx)
                        xls = pd.ExcelFile(tmp_xlsx, engine="openpyxl")
                        disponibles_lista = list(xls.sheet_names)
                        try:
                            os.remove(tmp_xlsx)
                        except Exception:
                            pass
                        last_exc = None
                        break
                    except Exception:
                        last_exc = exc
                        continue
                else:
                    last_exc = exc
                    continue
        if last_exc is not None:
            raise RuntimeError(f"No se pudo abrir el archivo {nombre_archivo}") from last_exc

        # Normalizador básico: recorta y compara case-insensitive
        def _norm(s: str) -> str:
            try:
                return (s or "").strip().casefold()
            except Exception:
                return str(s).strip().lower()

        disponibles_norm = {_norm(n): n for n in disponibles_lista}

        # Mapear hojas requeridas (posibles variantes de mayúsculas/espacios) a nombres reales del archivo
        requeridas_input = list(selecciones.keys())
        faltantes: List[str] = []
        hoja_real_por_norm: Dict[str, str] = {}
        for hoja_req in requeridas_input:
            clave = _norm(hoja_req)
            real = disponibles_norm.get(clave)
            if real is None:
                faltantes.append(hoja_req)
            else:
                hoja_real_por_norm[hoja_req] = real

        if faltantes:
            raise ValueError(
                f"Hojas inexistentes en el archivo: {sorted(faltantes)}. Disponibles: {disponibles_lista}"
            )

        # Validar configuraciones
        sheet_list: List[str] = []
        start_rows: Dict[str, int] = {}
        for hoja, cfg in selecciones.items():
            cfg_id = cfg.get("config_id")
            if cfg_id is None:
                raise ValueError(f"Falta config_id para la hoja '{hoja}'")
            config = ConfigImportacion.objects.filter(pk=cfg_id, proveedor=proveedor).first()
            if not config:
                raise ValueError(f"ConfigImportacion {cfg_id} no pertenece al proveedor o no existe")
            # La UI ahora muestra '#' iniciando en 0; usamos el valor tal cual (base-0)
            sr = int(cfg.get("start_row", 0))
            hoja_real = hoja_real_por_norm.get(hoja, hoja)
            sheet_list.append(hoja_real)
            start_rows[hoja_real] = sr

        # Generar CSVs con el servicio de conversión
        output_dir = os.path.dirname(file_path)
        out_paths = convertir_a_csv(
            file_path,
            output_dir=output_dir,
            sheet_name=sheet_list,
            start_row=start_rows,
        )
        # out_paths es lista de rutas alineada a sheet_list
        if not isinstance(out_paths, list):
            out_paths = [out_paths]

        hoja_a_csv = dict(zip(sheet_list, out_paths))

        creados: List[Tuple[str, str]] = []
        with transaction.atomic():
            for hoja, cfg in selecciones.items():
                cfg_id = int(cfg["config_id"])  # validado arriba
                config = ConfigImportacion.objects.get(pk=cfg_id)
                # Usar el nombre real de la hoja para mapear al CSV generado
                hoja_real = hoja_real_por_norm.get(hoja, hoja)
                csv_path = hoja_a_csv.get(hoja_real)
                if not csv_path:
                    # Fallback defensivo: si no se encuentra, intentar por nombre original
                    csv_path = hoja_a_csv.get(hoja)
                if not csv_path:
                    raise KeyError(f"No se pudo resolver ruta CSV para hoja '{hoja}' (resuelta='{hoja_real}'). Disponibles: {list(hoja_a_csv.keys())}")
                ap = ArchivoPendiente.objects.create(
                    proveedor=proveedor,
                    ruta_csv=csv_path,
                    hoja_origen=hoja_real,
                    nombre_archivo_origen=nombre_archivo,
                    config_usada=config,
                )
                creados.append((hoja_real, csv_path))

        # Borrar el archivo original (Excel/ODS) una vez generados los CSVs y creados los pendientes.
        # No borrar si el archivo ya era un .csv
        try:
            _, ext = os.path.splitext(nombre_archivo.lower())
            if ext != ".csv":
                # Usar el storage para borrar por nombre (respetando MEDIA_ROOT)
                self.storage.delete(nombre_archivo)
        except Exception:
            # Falla silenciosa: no bloquear el flujo por no poder borrar
            pass

        return creados

    def _col_to_index(self, value: Any, default: int) -> int:
        """Convierte letras de columna (A,B,...) o enteros/strings a índice 0-based."""
        if value is None:
            return default
        try:
            return int(value)
        except Exception:
            s = str(value).strip().upper()
            if not s:
                return default
            # Mapear letras a índice (A=0, B=1, ...)
            if s.isalpha():
                idx = 0
                for ch in s:
                    idx = idx * 26 + (ord(ch) - ord('A') + 1)
                return max(0, idx - 1)
            return default

    def procesar_pendientes(self) -> Dict[str, Any]:
        """
        Procesa todos los CSV pendientes en `ArchivoPendiente` (procesado=False)
        usando las configuraciones almacenadas. Marca como procesados al finalizar.
        """
        Proveedor, ConfigImportacion, ArchivoPendiente, PrecioDeLista, ArticuloSinRevisar, Descuento = self._load_models()

        from ..services.importador_csv import importar_csv

        pendientes = ArchivoPendiente.objects.select_related("proveedor", "config_usada").filter(procesado=False)
        try:
            logger.info("Procesando pendientes: count=%s", pendientes.count())
        except Exception:
            pass

        resultados: List[Dict[str, Any]] = []
        for ap in pendientes:
            proveedor = ap.proveedor
            config = ap.config_usada

            # Calcular índices de columnas a partir de la configuración
            col_codigo_idx = self._col_to_index(getattr(config, "col_codigo", None), 0)
            col_desc_idx = self._col_to_index(getattr(config, "col_descripcion", None), 1)
            col_precio_idx = self._col_to_index(getattr(config, "col_precio", None), 2)
            col_cant_idx = self._col_to_index(getattr(config, "col_cant", None), -1)
            if col_cant_idx < 0:
                col_cant_idx = None
            col_iva_idx = self._col_to_index(getattr(config, "col_iva", None), -1)
            if col_iva_idx < 0:
                col_iva_idx = None
            col_cod_barras_idx = self._col_to_index(getattr(config, "col_cod_barras", None), -1)
            if col_cod_barras_idx < 0:
                col_cod_barras_idx = None
            col_marca_idx = self._col_to_index(getattr(config, "col_marca", None), -1)
            if col_marca_idx < 0:
                col_marca_idx = None

            try:
                logger.info(
                    "Config columnas (letras): codigo=%s desc=%s precio=%s cant=%s iva=%s barras=%s marca=%s | índices (0-based): codigo=%s desc=%s precio=%s cant=%s iva=%s barras=%s marca=%s",
                    getattr(config, "col_codigo", None),
                    getattr(config, "col_descripcion", None),
                    getattr(config, "col_precio", None),
                    getattr(config, "col_cant", None),
                    getattr(config, "col_iva", None),
                    getattr(config, "col_cod_barras", None),
                    getattr(config, "col_marca", None),
                    col_codigo_idx,
                    col_desc_idx,
                    col_precio_idx,
                    (col_cant_idx if col_cant_idx is not None else None),
                    (col_iva_idx if col_iva_idx is not None else None),
                    (col_cod_barras_idx if col_cod_barras_idx is not None else None),
                    (col_marca_idx if col_marca_idx is not None else None),
                )
            except Exception:
                pass

            with transaction.atomic():
                stats = importar_csv(
                    proveedor=proveedor,
                    ruta_csv=ap.ruta_csv,
                    start_row=0,  # start_row ya fue aplicado al generar el CSV
                    col_codigo_idx=col_codigo_idx,
                    col_descripcion_idx=col_desc_idx,
                    col_precio_idx=col_precio_idx,
                    col_cant_idx=col_cant_idx,
                    col_iva_idx=col_iva_idx,
                    col_cod_barras_idx=col_cod_barras_idx,
                    col_marca_idx=col_marca_idx,
                    dry_run=False,
                )
                # marcar como procesado
                ap.procesado = True
                ap.save(update_fields=["procesado"])

            try:
                logger.info(
                    "Resultado importación: leidas=%s validas=%s descartadas=%s",
                    getattr(stats, "filas_leidas", None),
                    getattr(stats, "filas_validas", None),
                    getattr(stats, "filas_descartadas", None),
                )
            except Exception:
                pass

            resultados.append({
                "proveedor_id": proveedor.pk,
                "ruta_csv": ap.ruta_csv,
                "filas_leidas": getattr(stats, "filas_leidas", None),
                "filas_validas": getattr(stats, "filas_validas", None),
                "filas_descartadas": getattr(stats, "filas_descartadas", None),
            })

        return {"status": "ok", "procesados": len(resultados), "detalles": resultados}

    def procesar_excel(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:
        """
        Método heredado. Se recomienda usar `generar_csvs_por_hoja` + `procesar_pendientes`.
        Mantenido por compatibilidad: simplemente lista hojas y genera CSV para la primera hoja.
        """
        hojas = self.listar_hojas_excel(nombre_archivo)
        if not hojas:
            raise ValueError("El archivo no contiene hojas")
        # Intentar usar la primera configuración disponible del proveedor
        Proveedor, ConfigImportacion, *_ = self._load_models()
        proveedor = Proveedor.objects.get(pk=proveedor_id)
        config = ConfigImportacion.objects.filter(proveedor=proveedor).first()
        if not config:
            raise ValueError("No hay ConfigImportacion para el proveedor")
        self.generar_csvs_por_hoja(proveedor_id, nombre_archivo, {hojas[0]: {"config_id": config.pk, "start_row": 0}})
        return self.procesar_pendientes()