"""
Script CLI para ejecutar el procesamiento de Excel de un proveedor.

Uso:
    python src/importaciones/procesar_excel_script.py <proveedor_id> <ruta_excel>

El script inicializa Django, instancia ExcelRepository y llama a
`procesar_excel(proveedor_id, nombre_archivo)`.
"""

import os
import sys
import argparse
from pathlib import Path

# Asegurar que `src/` esté en sys.path y configurar settings
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_config.settings")

import django  # noqa: E402
from django.apps import apps  # noqa: E402

django.setup()

from importaciones.adapters.repository import ExcelRepository  # noqa: E402  # isort: skip


def main() -> None:
    parser = argparse.ArgumentParser(description="Procesar Excel de proveedor")
    parser.add_argument("proveedor_id", type=int, help="ID del proveedor")
    parser.add_argument("nombre_archivo", type=str, help="Ruta al archivo Excel")
    args = parser.parse_args()

    # Validar que el archivo exista
    file_path = Path(args.nombre_archivo)
    if not file_path.exists():
        print(f"Archivo no encontrado: {file_path}")
        sys.exit(1)

    # Ejecutar procesamiento
    repo = ExcelRepository()
    result = repo.procesar_excel(proveedor_id=args.proveedor_id, nombre_archivo=str(file_path))
    print(result)


if __name__ == "__main__":
    main()
