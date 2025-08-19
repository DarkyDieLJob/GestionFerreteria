# Archivo del repositorio del adaptador
"""
Repositorio del adaptador para el caso de uso de importación de Excel.

Implementa el puerto `ImportarExcelPort` del dominio de importaciones
usando Django ORM, pandas y almacenamiento de archivos del sistema.

Todas las lecturas/escrituras de base de datos se realizan contra
la base de datos "negocio_db".
"""

import os
from typing import Any, Dict, List, Tuple

import pandas as pd
from django.apps import apps
from django.core.files.storage import FileSystemStorage
from django.db import transaction

from ..domain.use_cases import ImportarExcelPort
from ..services.conversion import convertir_a_csv


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

    def vista_previa_excel(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:
        """
        Lee el Excel y devuelve las primeras 20 filas con las columnas disponibles.
        No realiza escrituras en base de datos.
        """
        file_path = self.storage.path(nombre_archivo)
        df = pd.read_excel(file_path)
        preview_rows: List[Dict[str, Any]] = df.head(20).fillna("").to_dict(orient="records")
        return {
            "proveedor_id": proveedor_id,
            "archivo": nombre_archivo,
            "columnas": list(df.columns),
            "filas": preview_rows,
            "total_filas": int(len(df)),
        }

    def listar_hojas_excel(self, nombre_archivo: str) -> List[str]:
        """Devuelve la lista de hojas disponibles en el Excel subido."""
        file_path = self.storage.path(nombre_archivo)
        try:
            xls = pd.ExcelFile(file_path)
        except Exception as exc:
            raise RuntimeError(f"No se pudo abrir el archivo {nombre_archivo}") from exc
        return list(xls.sheet_names)

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

        proveedor = Proveedor.objects.using("negocio_db").get(pk=proveedor_id)

        file_path = self.storage.path(nombre_archivo)
        # Validar existencia de hojas
        try:
            xls = pd.ExcelFile(file_path)
            disponibles = set(xls.sheet_names)
        except Exception as exc:
            raise RuntimeError(f"No se pudo abrir el archivo {nombre_archivo}") from exc

        requeridas = set(selecciones.keys())
        faltantes = requeridas - disponibles
        if faltantes:
            raise ValueError(f"Hojas inexistentes en el archivo: {sorted(faltantes)}")

        # Validar configuraciones
        sheet_list: List[str] = []
        start_rows: Dict[str, int] = {}
        for hoja, cfg in selecciones.items():
            cfg_id = cfg.get("config_id")
            if cfg_id is None:
                raise ValueError(f"Falta config_id para la hoja '{hoja}'")
            config = ConfigImportacion.objects.using("negocio_db").filter(pk=cfg_id, proveedor=proveedor).first()
            if not config:
                raise ValueError(f"ConfigImportacion {cfg_id} no pertenece al proveedor o no existe")
            sr = int(cfg.get("start_row", 0))
            sheet_list.append(hoja)
            start_rows[hoja] = sr

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
        with transaction.atomic(using="negocio_db"):
            for hoja, cfg in selecciones.items():
                cfg_id = int(cfg["config_id"])  # validado arriba
                config = ConfigImportacion.objects.using("negocio_db").get(pk=cfg_id)
                ap = ArchivoPendiente.objects.using("negocio_db").create(
                    proveedor=proveedor,
                    ruta_csv=hoja_a_csv[hoja],
                    hoja_origen=hoja,
                    config_usada=config,
                )
                creados.append((hoja, hoja_a_csv[hoja]))

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

        pendientes = ArchivoPendiente.objects.using("negocio_db").select_related("proveedor", "config_usada").filter(procesado=False)

        resultados: List[Dict[str, Any]] = []
        for ap in pendientes:
            proveedor = ap.proveedor
            config = ap.config_usada

            # Calcular índices de columnas a partir de la configuración
            col_codigo_idx = self._col_to_index(getattr(config, "col_codigo", None), 0)
            col_desc_idx = self._col_to_index(getattr(config, "col_descripcion", None), 1)
            col_precio_idx = self._col_to_index(getattr(config, "col_precio", None), 2)

            with transaction.atomic(using="negocio_db"):
                stats = importar_csv(
                    proveedor=proveedor,
                    ruta_csv=ap.ruta_csv,
                    start_row=0,  # start_row ya fue aplicado al generar el CSV
                    col_codigo_idx=col_codigo_idx,
                    col_descripcion_idx=col_desc_idx,
                    col_precio_idx=col_precio_idx,
                    dry_run=False,
                )
                # marcar como procesado
                ap.procesado = True
                ap.save(using="negocio_db", update_fields=["procesado"])

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
        proveedor = Proveedor.objects.using("negocio_db").get(pk=proveedor_id)
        config = ConfigImportacion.objects.using("negocio_db").filter(proveedor=proveedor).first()
        if not config:
            raise ValueError("No hay ConfigImportacion para el proveedor")
        self.generar_csvs_por_hoja(proveedor_id, nombre_archivo, {hojas[0]: {"config_id": config.pk, "start_row": 0}})
        return self.procesar_pendientes()