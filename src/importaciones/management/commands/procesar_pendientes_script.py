import os
from typing import Any

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction


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

        # Utilizar la base de datos 'negocio_db'
        qs = (
            ArchivoPendiente.objects.using("negocio_db")
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

            self.stdout.write(f"- {proveedor.nombre} :: {ap.hoja_origen} -> {ap.ruta_csv}")

            with transaction.atomic(using="negocio_db"):
                stats = importar_csv(
                    proveedor=proveedor,
                    ruta_csv=ap.ruta_csv,
                    start_row=0,  # start_row aplicado al generar el CSV
                    col_codigo_idx=col_codigo_idx,
                    col_descripcion_idx=col_desc_idx,
                    col_precio_idx=col_precio_idx,
                    dry_run=False,
                )
                ap.procesado = True
                ap.save(using="negocio_db", update_fields=["procesado"])

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
