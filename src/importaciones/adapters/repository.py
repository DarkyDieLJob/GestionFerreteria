# Archivo del repositorio del adaptador
"""
Repositorio del adaptador para el caso de uso de importación de Excel.

Implementa el puerto `ImportarExcelPort` del dominio de importaciones
usando Django ORM, pandas y almacenamiento de archivos del sistema.

Todas las lecturas/escrituras de base de datos se realizan contra
la base de datos "negocio_db".
"""

from typing import Any, Dict, List

import pandas as pd
from django.apps import apps
from django.core.files.storage import FileSystemStorage
from django.db import transaction

from ..domain.use_cases import ImportarExcelPort


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
        PrecioDeLista = apps.get_model("precios", "PrecioDeLista")
        ArticuloSinRevisar = apps.get_model("articulos", "ArticuloSinRevisar")
        Descuento = apps.get_model("precios", "Descuento")
        return Proveedor, ConfigImportacion, PrecioDeLista, ArticuloSinRevisar, Descuento

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

    def procesar_excel(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:
        """
        Procesa el Excel y crea/actualiza registros en `PrecioDeLista` y
        `ArticuloSinRevisar` usando `bulk_create` con `batch_size=1000`.

        Se ejecuta bajo una transacción atómica sobre `negocio_db` y elimina
        el archivo al finalizar el procesamiento exitosamente.
        """
        Proveedor, ConfigImportacion, PrecioDeLista, ArticuloSinRevisar, Descuento = self._load_models()

        file_path = self.storage.path(nombre_archivo)
        df = pd.read_excel(file_path)

        # Obtener proveedor y configuración de importación en negocio_db
        proveedor = Proveedor.objects.using("negocio_db").get(pk=proveedor_id)
        # La configuración puede definir mapeos de columnas, separadores, etc.
        config = (
            ConfigImportacion.objects.using("negocio_db").filter(proveedor=proveedor).first()
        )

        # Determinar nombres de columnas relevantes con fallback por defecto
        col_codigo = getattr(config, "columna_codigo", None) or "codigo"
        col_desc = getattr(config, "columna_descripcion", None) or "descripcion"
        col_precio = getattr(config, "columna_precio", None) or "precio"

        missing_cols = [c for c in [col_codigo, col_desc, col_precio] if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Columnas faltantes en Excel: {', '.join(missing_cols)}")

        df_work = df[[col_codigo, col_desc, col_precio]].copy()
        df_work.rename(columns={col_codigo: "codigo", col_desc: "descripcion", col_precio: "precio"}, inplace=True)

        # Normalizaciones básicas
        df_work["codigo"] = df_work["codigo"].astype(str).str.strip()
        df_work["descripcion"] = df_work["descripcion"].astype(str).str.strip()
        # Intentar convertir precio a número
        df_work["precio"] = pd.to_numeric(df_work["precio"], errors="coerce").fillna(0)

        crear_precios: List[Any] = []
        crear_asr: List[Any] = []

        with transaction.atomic(using="negocio_db"):
            # Construcción de objetos a crear en lote
            for row in df_work.itertuples(index=False):
                codigo = str(getattr(row, "codigo") or "").strip()
                descripcion = str(getattr(row, "descripcion") or "").strip()
                precio = getattr(row, "precio")

                if not codigo:
                    continue

                # PrecioDeLista: mantener un código normalizado con '/'
                codigo_norm = f"{codigo.rstrip('/')}/"

                crear_precios.append(
                    PrecioDeLista(
                        proveedor=proveedor,
                        codigo=codigo_norm,
                        descripcion=descripcion,
                        precio=precio,
                    )
                )

                # ArticuloSinRevisar: conservar código base sin '/'
                crear_asr.append(
                    ArticuloSinRevisar(
                        proveedor=proveedor,
                        codigo_proveedor=codigo.rstrip("/"),
                        descripcion_proveedor=descripcion,
                        precio=precio,
                    )
                )

            # Inserciones masivas
            # Si existen constraints de unicidad, `ignore_conflicts=True` evita errores por duplicados.
            if crear_precios:
                PrecioDeLista.objects.using("negocio_db").bulk_create(
                    crear_precios, batch_size=1000, ignore_conflicts=True
                )
            if crear_asr:
                ArticuloSinRevisar.objects.using("negocio_db").bulk_create(
                    crear_asr, batch_size=1000, ignore_conflicts=True
                )

        # Eliminar archivo una vez procesado con éxito
        try:
            self.storage.delete(nombre_archivo)
        except Exception:
            # Si falla la eliminación, no interrumpimos el flujo principal.
            pass

        return {
            "status": "ok",
            "proveedor_id": proveedor_id,
            "archivo": nombre_archivo,
            "creados_precio_de_lista": len(crear_precios),
            "creados_articulos_sin_revisar": len(crear_asr),
        }