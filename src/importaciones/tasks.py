from __future__ import annotations

from celery import shared_task


@shared_task(bind=True, name="importaciones.procesar_pendientes")
def procesar_pendientes_task(self):
    """Procesa los CSV pendientes encolados en ArchivoPendiente.

    Reutiliza la lógica existente del repositorio para mantener una sola fuente de verdad.
    """
    from importaciones.adapters.repository import ExcelRepository

    repo = ExcelRepository()
    result = repo.procesar_pendientes()
    return result
