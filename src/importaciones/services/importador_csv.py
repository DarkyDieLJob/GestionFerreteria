import csv
import re
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, Dict

from django.db import transaction
import logging

logger = logging.getLogger("importaciones.importador")

from proveedores.adapters.models import Proveedor
from precios.adapters.models import PrecioDeLista
from articulos.adapters.models import Articulo, ArticuloSinRevisar


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


def _parse_decimal_loose(raw: object) -> Optional[Decimal]:
    """Intenta extraer un número (entero o decimal) desde un string cualquiera.
    Acepta formatos con coma o punto decimal y contenido mixto ("x10", "10u").
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if s == "":
        return None
    # Buscar el primer número en el string
    m = re.search(r"[-+]?\d+(?:[\.,]\d+)?", s)
    if not m:
        return None
    num = m.group(0).replace(",", ".")
    try:
        return Decimal(num)
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
    col_cant_idx: Optional[int] = None,
    col_iva_idx: Optional[int] = None,
    col_cod_barras_idx: Optional[int] = None,
    col_marca_idx: Optional[int] = None,
    dry_run: bool = False,
) -> ImportStats:
    stats = ImportStats()

    logger.info(
        "Importando CSV: %s | proveedor_id=%s | idxs: codigo=%s desc=%s precio=%s cant=%s iva=%s barras=%s marca=%s",
        ruta_csv,
        getattr(proveedor, "pk", None),
        col_codigo_idx,
        col_descripcion_idx,
        col_precio_idx,
        col_cant_idx,
        col_iva_idx,
        col_cod_barras_idx,
        col_marca_idx,
    )

    for row_idx, row in leer_csv_en_filas(ruta_csv, start_row=start_row):
        stats.filas_leidas += 1
        # Expand row if short
        cols = list(row)
        # Extraer por indices; si falta índice, es inválida
        try:
            raw_codigo = cols[col_codigo_idx]
            raw_desc = cols[col_descripcion_idx]
            raw_precio = cols[col_precio_idx]
            raw_cant = cols[col_cant_idx] if (col_cant_idx is not None and col_cant_idx < len(cols)) else None
            raw_iva = cols[col_iva_idx] if (col_iva_idx is not None and col_iva_idx < len(cols)) else None
            raw_barras = cols[col_cod_barras_idx] if (col_cod_barras_idx is not None and col_cod_barras_idx < len(cols)) else None
            raw_marca = cols[col_marca_idx] if (col_marca_idx is not None and col_marca_idx < len(cols)) else None
        except IndexError:
            stats.filas_descartadas += 1
            continue

        codigo = (raw_codigo or "").strip()
        descripcion = (raw_desc or "").strip()
        precio = _parse_decimal(raw_precio)
        # cantidad opcional: usar decimal "flojo" para soportar distintos formatos
        bulto_val: Optional[Decimal] = _parse_decimal_loose(raw_cant) if raw_cant is not None else None
        # iva opcional: soportar 21 o 0.21 o "21%". Normalizar a fracción (0-1)
        iva_val: Optional[Decimal] = _parse_decimal_loose(raw_iva) if raw_iva is not None else None
        iva_norm: Optional[Decimal] = None
        if iva_val is not None:
            try:
                f = float(iva_val)
                if f > 1.5:  # valores como 21, 10.5
                    f = f / 100.0
                iva_norm = Decimal(str(f))
            except Exception:
                iva_norm = None
        # código de barras opcional
        codigo_barras = (str(raw_barras).strip() if raw_barras is not None else None) or None
        marca_str = (str(raw_marca).strip() if raw_marca is not None else None) or None

        logger.debug(
            "Fila %s: codigo='%s' precio=%s bulto_raw='%s' bulto_parsed=%s iva_raw='%s' iva_norm=%s barras='%s' marca='%s'",
            row_idx,
            codigo,
            precio,
            raw_cant,
            bulto_val,
            raw_iva,
            iva_norm,
            codigo_barras,
            marca_str,
        )

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
                # Actualizar bulto si vino cantidad en CSV
                if bulto_val is not None and bulto_val > 0 and pl.bulto != bulto_val:
                    logger.info(
                        "PL %s update: bulto %s -> %s (codigo=%s, proveedor=%s)",
                        getattr(pl, "pk", None),
                        pl.bulto,
                        bulto_val,
                        codigo_norm,
                        getattr(proveedor, "pk", None),
                    )
                    pl.bulto = bulto_val
                    changed = True
                if iva_norm is not None and pl.iva != iva_norm:
                    pl.iva = iva_norm
                    changed = True
                if marca_str is not None and pl.marca != marca_str:
                    pl.marca = marca_str
                    changed = True
                if changed:
                    pl.save()
                    logger.info(
                        "PL update: id=%s bulto=%s iva=%s marca='%s' (codigo=%s, proveedor=%s)",
                        getattr(pl, "pk", None),
                        pl.bulto,
                        pl.iva,
                        getattr(pl, "marca", None),
                        codigo_norm,
                        getattr(proveedor, "pk", None),
                    )
                    stats.actualizadas += 1
            else:
                pl = PrecioDeLista.objects.create(
                    proveedor=proveedor,
                    codigo=codigo_norm,
                    descripcion=descripcion,
                    precio=precio,
                    bulto=(bulto_val if bulto_val is not None else 1),
                    iva=(iva_norm if iva_norm is not None else Decimal("0.21")),
                    marca=marca_str,
                )
                logger.info(
                    "PL create: id=%s bulto=%s iva=%s marca='%s' (codigo=%s, proveedor=%s)",
                    getattr(pl, "pk", None),
                    pl.bulto,
                    pl.iva,
                    getattr(pl, "marca", None),
                    codigo_norm,
                    getattr(proveedor, "pk", None),
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
                # Mantener descripcion_proveedor existente, solo actualizar precio
                if asr.precio != precio:
                    asr.precio = precio
                    changed_asr = True
                # Actualizar código de barras si provisto
                if codigo_barras and asr.codigo_barras != codigo_barras:
                    asr.codigo_barras = codigo_barras
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
                    codigo_barras=codigo_barras if codigo_barras else None,
                )

            # Asegurar ArticuloProveedor por cada PrecioDeLista (inicialmente vinculado a ASR)
            from articulos.adapters.models import ArticuloProveedor as AP
            qs_ap = AP.objects.filter(precio_de_lista=pl).order_by("id")
            if qs_ap.exists():
                ap = qs_ap.first()
                # Eliminar duplicados si existieran (defensa histórica)
                extra_ids = list(qs_ap.values_list("id", flat=True))[1:]
                if extra_ids:
                    AP.objects.filter(id__in=extra_ids).delete()
                # Actualizar datos desde PL/ASR (si no está mapeado a Articulo)
                changed_ap = False
                if ap.codigo_proveedor != codigo_prov_norm:
                    ap.codigo_proveedor = codigo_prov_norm
                    changed_ap = True
                if ap.precio != precio:
                    ap.precio = precio
                    changed_ap = True
                # Mantener stock y descripcion_proveedor existentes
                if ap.articulo is None and ap.articulo_s_revisar_id != asr.id:
                    ap.articulo_s_revisar = asr
                    changed_ap = True
                if ap.proveedor_id != proveedor.id:
                    ap.proveedor = proveedor
                    changed_ap = True
                # Sincronizar flag dividir desde PrecioDeLista si existe ese campo
                try:
                    pl_dividir = getattr(pl, "dividir")
                except Exception:
                    pl_dividir = None
                if pl_dividir is not None and getattr(ap, "dividir", None) != pl_dividir:
                    ap.dividir = pl_dividir
                    changed_ap = True
                # Si hay código de barras, crear/mantener Articulo definitivo y mapear AP
                if codigo_barras:
                    art, created_art = Articulo.objects.get_or_create(
                        codigo_barras=codigo_barras,
                        defaults={
                            "nombre": descripcion[:200] or codigo_prov_norm,
                            "descripcion": descripcion,
                        },
                    )
                    if created_art:
                        logger.info("Articulo create: id=%s codigo_barras=%s", getattr(art, "pk", None), codigo_barras)
                    if ap.articulo_id != art.id:
                        ap.articulo = art
                        ap.articulo_s_revisar = None
                        changed_ap = True
                    # Deshabilitar ASR: marcar estado como 'mapeado' si existe ese choice
                    try:
                        if asr and getattr(asr, "estado", None) != "mapeado":
                            asr.estado = "mapeado"
                            asr.save(update_fields=["estado"])
                    except Exception:
                        pass
                if changed_ap:
                    ap.save()
            else:
                if codigo_barras:
                    art, created_art = Articulo.objects.get_or_create(
                        codigo_barras=codigo_barras,
                        defaults={
                            "nombre": descripcion[:200] or codigo_prov_norm,
                            "descripcion": descripcion,
                        },
                    )
                    if created_art:
                        logger.info("Articulo create: id=%s codigo_barras=%s", getattr(art, "pk", None), codigo_barras)
                    # Deshabilitar ASR si se creó
                    try:
                        if asr and getattr(asr, "estado", None) != "mapeado":
                            asr.estado = "mapeado"
                            asr.save(update_fields=["estado"])
                    except Exception:
                        pass
                    AP.objects.create(
                        articulo=art,
                        articulo_s_revisar=None,
                        proveedor=proveedor,
                        precio_de_lista=pl,
                        codigo_proveedor=codigo_prov_norm,
                        descripcion_proveedor=descripcion,
                        precio=precio,
                        stock=asr.stock,
                        dividir=getattr(pl, "dividir", False),
                    )
                else:
                    AP.objects.create(
                        articulo=None,
                        articulo_s_revisar=asr,
                        proveedor=proveedor,
                        precio_de_lista=pl,
                        codigo_proveedor=codigo_prov_norm,
                        descripcion_proveedor=descripcion,
                        precio=precio,
                        stock=asr.stock,
                        dividir=getattr(pl, "dividir", False),
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
