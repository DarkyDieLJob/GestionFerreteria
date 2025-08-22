import os
import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction

logger = logging.getLogger("importaciones.cmd")


class Command(BaseCommand):
    help = "Procesa todos los CSV pendientes en ArchivoPendiente (procesado=False) y los elimina al finalizar."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Cantidad máxima de pendientes a procesar en esta ejecución.",
        )

    def handle(self, *args: Any, **options: Any):
        ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
        ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")
        Proveedor = apps.get_model("proveedores", "Proveedor")

        # Importador CSV
        from importaciones.services.importador_csv import importar_csv

        # Usar siempre la base por defecto
        qs = (
            ArchivoPendiente.objects
            .select_related("proveedor", "config_usada")
            .filter(procesado=False)
            .order_by("fecha_subida")
        )
        limit = options.get("limit")
        if limit:
            qs = qs[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No hay archivos pendientes para procesar."))
            return

        self.stdout.write(self.style.NOTICE(f"Procesando {total} pendiente(s)..."))

        def col_to_index(value, default):
            if value is None:
                return default
            try:
                return int(value)
            except Exception:
                s = str(value).strip().upper()
                if not s:
                    return default
                if s.isalpha():
                    idx = 0
                    for ch in s:
                        idx = idx * 26 + (ord(ch) - ord("A") + 1)
                    return max(0, idx - 1)
                return default

        procesados = 0
        for ap in qs:
            proveedor = ap.proveedor  # type: Proveedor
            config = ap.config_usada  # type: ConfigImportacion

            col_codigo_idx = col_to_index(getattr(config, "col_codigo", None), 0)
            col_desc_idx = col_to_index(getattr(config, "col_descripcion", None), 1)
            col_precio_idx = col_to_index(getattr(config, "col_precio", None), 2)
            col_cant_idx = col_to_index(getattr(config, "col_cant", None), -1)
            if col_cant_idx < 0:
                col_cant_idx = None
            col_iva_idx = col_to_index(getattr(config, "col_iva", None), -1)
            if col_iva_idx < 0:
                col_iva_idx = None
            col_cod_barras_idx = col_to_index(getattr(config, "col_cod_barras", None), -1)
            if col_cod_barras_idx < 0:
                col_cod_barras_idx = None
            col_marca_idx = col_to_index(getattr(config, "col_marca", None), -1)
            if col_marca_idx < 0:
                col_marca_idx = None

            self.stdout.write(f"- {proveedor.nombre} :: {ap.hoja_origen} -> {ap.ruta_csv}")
            try:
                logger.info(
                    "Idxs usados (0-based): codigo=%s desc=%s precio=%s cant=%s iva=%s barras=%s marca=%s | letras: codigo=%s desc=%s precio=%s cant=%s iva=%s barras=%s marca=%s",
                    col_codigo_idx,
                    col_desc_idx,
                    col_precio_idx,
                    (col_cant_idx if col_cant_idx is not None else None),
                    (col_iva_idx if col_iva_idx is not None else None),
                    (col_cod_barras_idx if col_cod_barras_idx is not None else None),
                    (col_marca_idx if col_marca_idx is not None else None),
                    getattr(config, "col_codigo", None),
                    getattr(config, "col_descripcion", None),
                    getattr(config, "col_precio", None),
                    getattr(config, "col_cant", None),
                    getattr(config, "col_iva", None),
                    getattr(config, "col_cod_barras", None),
                    getattr(config, "col_marca", None),
                )
            except Exception:
                pass

            with transaction.atomic():
                stats = importar_csv(
                    proveedor=proveedor,
                    ruta_csv=ap.ruta_csv,
                    start_row=0,  # start_row aplicado al generar el CSV
                    col_codigo_idx=col_codigo_idx,
                    col_descripcion_idx=col_desc_idx,
                    col_precio_idx=col_precio_idx,
                    col_cant_idx=col_cant_idx,
                    col_iva_idx=col_iva_idx,
                    col_cod_barras_idx=col_cod_barras_idx,
                    col_marca_idx=col_marca_idx,
                    dry_run=False,
                )
                ap.procesado = True
                ap.save(update_fields=["procesado"])

            # Intentar borrar el archivo CSV
            try:
                if ap.ruta_csv and os.path.exists(ap.ruta_csv):
                    os.remove(ap.ruta_csv)
            except Exception as exc:
                self.stderr.write(self.style.WARNING(f"No se pudo eliminar {ap.ruta_csv}: {exc}"))

            self.stdout.write(
                self.style.SUCCESS(
                    f"  OK - leidas={getattr(stats, 'filas_leidas', '-')}, validas={getattr(stats, 'filas_validas', '-')}, descartadas={getattr(stats, 'filas_descartadas', '-')}"
                )
            )
            procesados += 1

        self.stdout.write(self.style.SUCCESS(f"Finalizado. Pendientes procesados: {procesados}"))
