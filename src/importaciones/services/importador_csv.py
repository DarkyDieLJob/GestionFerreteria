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
            # Normalizar código para respetar la unicidad como la aplica PrecioDeLista.save()
            codigo_norm = _normalizar_codigo_precio(codigo)

            # Upsert PrecioDeLista con clave exacta (proveedor, codigo_norm).
            # Si hay duplicados históricos para esa clave, mantener el primero y eliminar el resto.
            qs_pl = (
                PrecioDeLista.objects
                .filter(proveedor=proveedor, codigo=codigo_norm)
                .order_by("id")
            )
            if qs_pl.exists():
                pl = qs_pl.first()
                # Eliminar duplicados restantes
                dup_ids = list(qs_pl.values_list("id", flat=True))[1:]
                if dup_ids:
                    PrecioDeLista.objects.filter(id__in=dup_ids).delete()
                # Actualizar
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
                pl = PrecioDeLista.objects.create(
                    proveedor=proveedor,
                    codigo=codigo_norm,
                    descripcion=descripcion,
                    precio=precio,
                )
                stats.creadas += 1

            # Si no hay mapeo a Articulo definitivo, lo dejamos como ArticuloSinRevisar
            # Evitar MultipleObjectsReturned: usar filter().first() por posibles duplicados históricos
            codigo_prov_norm = _normalizar_codigo_precio(codigo)
            asr = (
                ArticuloSinRevisar.objects
                .filter(proveedor=proveedor, codigo_proveedor__startswith=codigo_prov_norm)
                .order_by("id")
                .first()
            )
            if asr:
                changed_asr = False
                if asr.descripcion_proveedor != descripcion:
                    asr.descripcion_proveedor = descripcion
                    changed_asr = True
                if asr.precio != precio:
                    asr.precio = precio
                    changed_asr = True
                if changed_asr:
                    asr.save()
            else:
                asr = ArticuloSinRevisar.objects.create(
                    proveedor=proveedor,
                    codigo_proveedor=codigo_prov_norm,
                    descripcion_proveedor=descripcion,
                    precio=precio,
                    stock=0,
                )

            # Asegurar ArticuloProveedor por cada PrecioDeLista (inicialmente vinculado a ASR)
            from articulos.adapters.models import ArticuloProveedor as AP
            qs_ap = AP.objects.using("negocio_db").filter(precio_de_lista=pl).order_by("id")
            if qs_ap.exists():
                ap = qs_ap.first()
                # Eliminar duplicados si existieran (defensa histórica)
                extra_ids = list(qs_ap.values_list("id", flat=True))[1:]
                if extra_ids:
                    AP.objects.using("negocio_db").filter(id__in=extra_ids).delete()
                # Actualizar datos desde PL/ASR (si no está mapeado a Articulo)
                changed_ap = False
                if ap.codigo_proveedor != codigo_prov_norm:
                    ap.codigo_proveedor = codigo_prov_norm
                    changed_ap = True
                if ap.descripcion_proveedor != descripcion:
                    ap.descripcion_proveedor = descripcion
                    changed_ap = True
                if ap.precio != precio:
                    ap.precio = precio
                    changed_ap = True
                if ap.stock != asr.stock:
                    ap.stock = asr.stock
                    changed_ap = True
                if ap.articulo is None and ap.articulo_s_revisar_id != asr.id:
                    ap.articulo_s_revisar = asr
                    changed_ap = True
                if ap.proveedor_id != proveedor.id:
                    ap.proveedor = proveedor
                    changed_ap = True
                if changed_ap:
                    ap.save(using="negocio_db")
            else:
                # Crear AP inicial apuntando a ASR
                AP.objects.using("negocio_db").create(
                    articulo=None,
                    articulo_s_revisar=asr,
                    proveedor=proveedor,
                    precio_de_lista=pl,
                    codigo_proveedor=codigo_prov_norm,
                    descripcion_proveedor=descripcion,
                    precio=precio,
                    stock=asr.stock,
                    dividir=False,
                )

    return stats


def _normalizar_codigo_precio(codigo: str) -> str:
    """Replica la normalización que realiza PrecioDeLista.save().

    - Quita la barra final si existe
    - Intenta remover ceros a la izquierda interpretando como int
    - Vuelve a añadir la barra de cierre
    """
    s = (codigo or "").rstrip("/")
    try:
        s = str(int(s.lstrip("0")))
    except ValueError:
        # Si no es numérico, conservar como venga (sin barra final)
        pass
    return f"{s}/"
