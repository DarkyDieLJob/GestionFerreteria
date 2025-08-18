"""
Programador diario para procesar archivos Excel de proveedores a las 00:00.

Usa la librería `schedule` para ejecutar cada día a las 00:00 una tarea que:
- Busca proveedores en la base `negocio_db`.
- Revisa si existe un archivo pendiente en BASE_DIR / 'data/imports' con
  el patrón excel_<proveedor_id>.xlsx.
- Invoca un script CLI que ejecuta el procesamiento mediante ExcelRepository.

Ejecutar con:
    python src/core_config/scheduler.py

Nota: Este módulo inicializa Django para poder acceder a modelos y settings.
Además, ArticuloSinRevisar no utiliza un campo 'usuario'; el procesamiento no
depende de ninguna relación con auth_user.
"""

import os
import sys
import time
import subprocess
from pathlib import Path


# Configurar entorno Django (añadir src al sys.path y cargar settings)
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]  # .../src/
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_config.settings")

import django  # noqa: E402
from django.apps import apps  # noqa: E402
from django.conf import settings  # noqa: E402

django.setup()


def run_procesar_excel() -> None:
    """
    Recorre todos los proveedores y dispara el procesamiento si existe
    un archivo excel_<proveedor_id>.xlsx en BASE_DIR/data/imports.
    """
    Proveedor = apps.get_model("proveedores", "Proveedor")

    imports_dir = Path(settings.BASE_DIR) / "data" / "imports"
    imports_dir.mkdir(parents=True, exist_ok=True)

    for prov in Proveedor.objects.using("negocio_db").all():
        file_name = f"excel_{prov.id}.xlsx"
        file_path = imports_dir / file_name
        if file_path.exists():
            # Ejecuta el script de procesamiento como subproceso para aislar el trabajo
            cmd = [
                sys.executable,
                str(SRC_DIR / "importaciones" / "procesar_excel_script.py"),
                str(prov.id),
                str(file_path),
            ]
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as exc:
                # Continuar con otros proveedores aunque uno falle
                print(f"Fallo al procesar proveedor {prov.id}: {exc}")


def main() -> None:
    # Programar la tarea diaria a las 00:00 (import perezoso de schedule)
    try:
        import schedule  # type: ignore
    except ModuleNotFoundError:
        print("La librería 'schedule' no está instalada. Instálala para usar el scheduler.")
        return
    schedule.every().day.at("00:00").do(run_procesar_excel)

    print("Scheduler iniciado. Verificando tareas cada minuto...")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
