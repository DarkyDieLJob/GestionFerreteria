import os
import tempfile
from typing import Optional


def _get_pandas():
    """Importa pandas de forma perezosa. Se separa para poder mockearlo en tests."""
    import pandas as pd  # type: ignore
    return pd


def convertir_a_csv(
    input_path: str,
    output_dir: Optional[str] = None,
    sheet: int | str = 0,
    encoding: str = "utf-8",
    decimal: str = ".",
    delimiter: str = ",",
) -> str:
    """
    Convierte una planilla (xls, xlsx, ods) a CSV. Si ya es CSV, devuelve el mismo path.

    - Trabaja por posiciones (header=None más adelante en el importador).
    - No normaliza encabezados.
    - 'sheet' puede ser índice o nombre.

    Retorna la ruta al CSV generado (o el mismo input si ya era .csv).
    """
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".csv":
        return input_path

    # Importar pandas de forma perezosa para no agregar dependencia si no se usa
    try:
        pd = _get_pandas()
    except Exception as exc:  # pragma: no cover - error claro si no está
        raise RuntimeError("pandas es requerido para convertir a CSV") from exc

    engine = None
    if ext == ".xlsx":
        engine = "openpyxl"
    elif ext == ".xls":
        engine = "xlrd"
    elif ext == ".ods":
        engine = "odf"
    else:
        raise ValueError(f"Formato no soportado para conversión: {ext}")

    try:
        df = pd.read_excel(input_path, header=None, sheet_name=sheet, engine=engine)
    except Exception as exc:
        raise RuntimeError(
            f"No se pudo leer el archivo {input_path} con engine='{engine}'. "
            "Verifique que las dependencias estén instaladas (openpyxl para xlsx, xlrd para xls, odfpy para ods)."
        ) from exc

    if output_dir is None:
        output_dir = os.path.dirname(input_path) or tempfile.gettempdir()

    base = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join(output_dir, f"{base}.csv")

    # Guardar CSV con el delimitador/encoding/decimal solicitados
    try:
        df.to_csv(out_path, index=False, header=False, encoding=encoding)
    except Exception as exc:
        raise RuntimeError(f"No se pudo escribir el CSV en {out_path}") from exc

    return out_path
