from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict


def _to_dec(val: Any) -> Decimal:
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0")


def _normalize_factor_or_percent(val: Any) -> Decimal:
    """
    Normaliza un valor que puede venir en factor (0<d<1) o porcentaje (1..100) a factor [0..1].
    Reglas:
    - (0,1): se usa tal cual.
    - [1..100]: se divide por 100.
    - <=0 o ==1: se considera sin efecto => 0.
    """
    d = _to_dec(val)
    if d > Decimal("1") and d <= Decimal("100"):
        return d / Decimal("100")
    if d <= Decimal("0"):
        return Decimal("0")
    if d == Decimal("1"):
        return Decimal("0")
    return d  # ya es factor (0<d<1)


def round_money(amount: Decimal) -> Decimal:
    """Redondeo final de importes (2 decimales). Preparado para lógica especial futura."""
    # Nota futura: aquí podría aplicarse la regla de negocio especial
    # (p.ej., si múltiplo de 1000 entonces -50) antes del redondeo.
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_prices(
    *,
    precio_de_lista: Any,
    iva: Any,
    proveedor_desc_com: Any,
    proveedor_margen: Any,
    proveedor_margen_ef: Any,
    descuento_general: Any,
    descuento_activo: bool,
    descuento_bulto: Any,
    descuento_cantidad_bulto: Any,
    bulto_articulo: Any,
    cantidad: Any,
    dividir: bool,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Calculadora pura del pipeline de precios.

    Orden actual:
    base (IVA y descuento comercial) -> márgenes -> precio por bulto del artículo ->
    descuento por bulto (si >0) -> descuento general (si activo) -> margen efectivo -> redondeo final.
    """
    precio_de_lista = _to_dec(precio_de_lista)
    iva_dec = _to_dec(iva)
    desc_com = _to_dec(proveedor_desc_com)
    margen = _to_dec(proveedor_margen)
    margen_ef = _to_dec(proveedor_margen_ef)
    gen = _to_dec(descuento_general) if descuento_activo else Decimal("0")

    qty = _to_dec(cantidad)
    threshold = int(_to_dec(descuento_cantidad_bulto)) if descuento_cantidad_bulto is not None else 1
    bulto = _to_dec(bulto_articulo) or Decimal("1")

    # base: precio lista (+iva) * (1 - desc_comercial)
    if dividir and bulto > 0:
        base = (precio_de_lista / bulto) * (Decimal("1") + iva_dec) * (Decimal("1") - desc_com)
    else:
        base = precio_de_lista * (Decimal("1") + iva_dec) * (Decimal("1") - desc_com)

    # unitario con margen
    final_unit = base * margen

    # bulto del artículo (precio previo a desc por bulto)
    bulto_monto = final_unit * bulto
    bulto_qty = int(bulto or 1)

    # Descuento por bulto: si no hay umbral (None o <=1) aplica siempre a totales de bulto.
    # Si hay umbral (>1), considerar alcanzado si la compra por pack (bulto_qty) o la cantidad solicitada alcanza el umbral.
    bulk_percent = _to_dec(descuento_bulto) if descuento_bulto is not None else Decimal("0")
    has_bulk = bulk_percent > Decimal("0")
    no_threshold = (threshold is None) or (threshold <= 1)
    meets_threshold = (qty >= threshold) or (bulto_qty >= threshold)
    apply_bulk = bool(has_bulk and (no_threshold or meets_threshold))
    factor_bulto = (Decimal("1") - (bulk_percent / Decimal("100"))) if apply_bulk else Decimal("1")

    # descuento general (si activo)
    if descuento_activo and gen > 0:
        # gen puede venir como factor (0<d<1) o porcentaje (1..100); normalizamos a factor
        gen_factor = _normalize_factor_or_percent(gen)
        final_unit = final_unit * (Decimal("1") - gen_factor)

    # Totales para compra por bulto (cantidad de unidades = bulto)
    bulto_monto = base * bulto_qty
    # Aplicar factor_bulto sólo a los totales de bulto
    final_bulto = final_unit * bulto_qty * factor_bulto
    final_bulto_ef = (final_unit * margen_ef) * bulto_qty * factor_bulto

    # redondeo final
    result = {
        "base": round_money(base),
        "final": round_money(final_unit),
        "final_efectivo": round_money(final_unit * margen_ef),
        "bulto": round_money(bulto_monto),
        "final_bulto": round_money(final_bulto),
        "final_bulto_efectivo": round_money(final_bulto_ef),
        "cantidad_bulto_aplicada": int(qty or 0),
        # Campos no-debug para UI
        "cantidad_bulto_articulo": int(bulto),
        "umbral_descuento_bulto": int(threshold or 0),
    }

    # Incluir siempre claves de debug esperadas por plantillas, controlando el contenido
    # por el flag 'debug'. Si no hay debug, igualmente exponemos valores útiles.
    result.update({
        # alias/valores esperados por plantillas existentes
        "debug_descuento_bulto": float(bulk_percent),
        "debug_factor_descuento_bulto": float(factor_bulto),
        "debug_bulto_articulo": int(bulto),
        "debug_cantidad": float(qty),
        "debug_cantidad_bulto_politica": int(threshold or 0),
        "debug_aplica_descuento_bulto": bool(apply_bulk),
        "debug_min_qty": int(threshold or 0),
        "debug_applied_qty": float(qty),
    })

    return result
