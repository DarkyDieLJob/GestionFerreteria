import csv
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, Dict

from django.db import transaction

from proveedores.adapters.models import Proveedor
from precios.adapters.models import PrecioDeLista
from articulos.adapters.models import ArticuloSinRevisar


@dataclass
class ImportStats:
    filas_leidas: int = 0
    filas_validas: int = 0
    filas_descartadas: int = 0
    creadas: int = 0
    actualizadas: int = 0


def _parse_decimal(valor: str) -> Optional[Decimal]:
    if valor is None:
        return None
    s = str(valor).strip()
    if s == "":
        return None
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def leer_csv_en_filas(ruta_csv: str, start_row: int) -> Iterable[Tuple[int, list]]:
    with open(ruta_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=",")
        for idx, row in enumerate(reader, start=1):
            if idx < start_row:
                continue
            yield idx, row


def importar_csv(
    proveedor: Proveedor,
    ruta_csv: str,
    start_row: int,
    col_codigo_idx: int,
    col_descripcion_idx: int,
    col_precio_idx: int,
    dry_run: bool = False,
) -> ImportStats:
    stats = ImportStats()

    for row_idx, row in leer_csv_en_filas(ruta_csv, start_row=start_row):
        stats.filas_leidas += 1
        # Expand row if short
        cols = list(row)
        # Extraer por indices; si falta índice, es inválida
        try:
            raw_codigo = cols[col_codigo_idx]
            raw_desc = cols[col_descripcion_idx]
            raw_precio = cols[col_precio_idx]
        except IndexError:
            stats.filas_descartadas += 1
            continue

        codigo = (raw_codigo or "").strip()
        descripcion = (raw_desc or "").strip()
        precio = _parse_decimal(raw_precio)

        if not codigo or not descripcion or precio is None:
            stats.filas_descartadas += 1
            continue

        stats.filas_validas += 1

        if dry_run:
            # No escribimos nada
            continue

        with transaction.atomic():
            # Upsert PrecioDeLista por (proveedor, codigo)
            pl, created = PrecioDeLista.objects.get_or_create(
                proveedor=proveedor,
                codigo=codigo,
                defaults={
                    "descripcion": descripcion,
                    "precio": precio,
                },
            )
            if not created:
                # Actualizamos si cambió algo
                changed = False
                if pl.descripcion != descripcion:
                    pl.descripcion = descripcion
                    changed = True
                if pl.precio != precio:
                    pl.precio = precio
                    changed = True
                if changed:
                    pl.save()
                    stats.actualizadas += 1
                else:
                    # No cambios relevantes
                    pass
            else:
                stats.creadas += 1

            # Si no hay mapeo a Articulo definitivo, lo dejamos como ArticuloSinRevisar
            ArticuloSinRevisar.objects.get_or_create(
                proveedor=proveedor,
                codigo_proveedor=codigo,
                defaults={
                    "descripcion_proveedor": descripcion,
                    "precio": precio,
                    "stock": 0,
                },
            )

    return stats
