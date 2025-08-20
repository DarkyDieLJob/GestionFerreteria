# Archivo del repositorio del adaptador
"""
Implementaciones de repositorios (adaptadores) para la arquitectura hexagonal
del contexto "articulos". Estas clases implementan los puertos definidos en
src/articulos/domain/interfaces.py utilizando Django ORM.

Todas las consultas se realizan contra la base de datos "negocio_db".
"""

from typing import Any, Dict, List, Optional

from django.apps import apps
from django.db.models import QuerySet
from django.utils import timezone

from ..domain.interfaces import (
    CalcularPrecioPort,
    BuscarArticuloPort,
    MapearArticuloPort,
)


def _normalize_code_and_abbr(query: str, abreviatura: Optional[str] = None) -> Dict[str, Optional[str]]:
    """
    Normaliza el código base y resuelve abreviatura si viene embebida.

    - Elimina ceros a la izquierda del código base.
    - Asegura que termine con '/'.
    - Si `query` incluye una abreviatura (p.ej. "37/Vj"), la extrae si `abreviatura` no fue provista.
    """
    raw = (query or "").strip()
    abbr = abreviatura.strip() if isinstance(abreviatura, str) and abreviatura.strip() else None

    base = raw
    if "/" in raw:
        parts = raw.split("/")
        # última parte puede ser abreviatura
        if len(parts[-1]) > 0 and not raw.endswith("/"):
            possible_abbr = parts[-1]
            base = "/".join(parts[:-1])
            if not abbr:
                abbr = possible_abbr
        else:
            base = raw.rstrip("/")
    else:
        base = raw

    # strip leading zeros
    try:
        base_int = str(int(base.lstrip("0")))
    except ValueError:
        base_int = base

    code = f"{base_int}/"
    abbr = abbr.upper() if abbr else None
    return {"code": code, "abbr": abbr}


class PrecioRepository(CalcularPrecioPort):
    """
    Implementación del puerto `CalcularPrecioPort` usando Django ORM.

    Calcula precios dinámicos delegando en los métodos del modelo.
    """

    def calcular_precios(self, articulo_id: Any, tipo: str, cantidad: int, pago_efectivo: bool) -> Dict[str, Any]:
        if tipo == "articulo":
            ArticuloProveedor = apps.get_model("articulos", "ArticuloProveedor")
            ap = (
                ArticuloProveedor.objects.using("negocio_db").select_related("proveedor", "precio_de_lista").get(
                    pk=articulo_id
                )
            )
            return ap.generar_precios(cantidad=cantidad, pago_efectivo=pago_efectivo)
        if tipo == "sin_revisar":
            ArticuloSinRevisar = apps.get_model("articulos", "ArticuloSinRevisar")
            asr = ArticuloSinRevisar.objects.using("negocio_db").select_related("proveedor", "descuento").get(
                pk=articulo_id
            )
            return asr.generar_precios(cantidad=cantidad, pago_efectivo=pago_efectivo)
        raise ValueError("tipo inválido: use 'articulo' o 'sin_revisar'")


class BusquedaRepository(BuscarArticuloPort):
    """
    Implementación del puerto `BuscarArticuloPort` usando Django ORM.

    Busca en PrecioDeLista, ArticuloSinRevisar y ArticuloProveedor
    contra la base de datos "negocio_db".
    """

    def buscar_articulos(self, query: str, abreviatura: Optional[str] = None) -> List[Dict[str, Any]]:
        norm = _normalize_code_and_abbr(query, abreviatura)
        code: str = norm["code"] or ""
        abbr: Optional[str] = norm["abbr"]

        # Solo devolvemos ArticuloProveedor en los resultados
        ArticuloProveedor = apps.get_model("articulos", "ArticuloProveedor")

        results: List[Dict[str, Any]] = []

        # Prefijo a buscar (sin la barra final) para permitir coincidencias por inicio
        prefix = code.rstrip("/")

        # ArticuloProveedor: buscar por codigo_proveedor y abreviatura
        base_no_slash = prefix
        qs_ap: QuerySet = ArticuloProveedor.objects.using("negocio_db").select_related(
            "proveedor", "precio_de_lista", "articulo"
        )
        qs_ap = qs_ap.filter(codigo_proveedor__istartswith=base_no_slash).order_by("codigo_proveedor")
        if abbr:
            qs_ap = qs_ap.filter(proveedor__abreviatura__iexact=abbr)
        for ap in qs_ap[:50]:
            codigo = getattr(ap, "get_codigo_completo", lambda: f"{ap.codigo_proveedor}/{ap.proveedor.abreviatura}")()
            precios_calc = ap.generar_precios(cantidad=1, pago_efectivo=False)
            puede_mapear = ap.articulo_id is None
            pendiente_id = ap.articulo_s_revisar_id if puede_mapear else None
            results.append(
                {
                    "id": ap.id,
                    "tipo": "articulo_proveedor",
                    "codigo": ap.get_codigo_completo(),
                    "descripcion": ap.descripcion_proveedor,
                    "proveedor": ap.proveedor.abreviatura,
                    "precios": {
                        "base": float(precios_calc.get("base", 0)),
                        "final": float(precios_calc.get("final", 0)),
                        "final_efectivo": float(precios_calc.get("final_efectivo", 0)),
                        "bulto": float(precios_calc.get("bulto", 0)),
                        "final_bulto": float(precios_calc.get("final_bulto", 0)),
                        "final_bulto_efectivo": float(precios_calc.get("final_bulto_efectivo", 0)),
                        "cantidad_bulto_aplicada": int(precios_calc.get("cantidad_bulto_aplicada", 1)),
                        "descuento_tipo": (ap.descuento.tipo if getattr(ap, "descuento", None) else "Sin Descuento"),
                        # Debug fields (passthrough si existen)
                        "debug_descuento_bulto": precios_calc.get("debug_descuento_bulto"),
                        "debug_cantidad_bulto_politica": precios_calc.get("debug_cantidad_bulto_politica"),
                        "debug_bulto_articulo": precios_calc.get("debug_bulto_articulo"),
                        "debug_min_qty": precios_calc.get("debug_min_qty"),
                        "debug_applied_qty": precios_calc.get("debug_applied_qty"),
                        "debug_aplica_descuento_bulto": precios_calc.get("debug_aplica_descuento_bulto"),
                        "debug_factor_descuento_bulto": precios_calc.get("debug_factor_descuento_bulto"),
                    },
                    "puede_mapear": puede_mapear,
                    "pendiente_id": pendiente_id,
                }
            )

        return results


class MapeoRepository(MapearArticuloPort):
    """
    Implementación del puerto `MapearArticuloPort` usando Django ORM.

    Mapea un ArticuloSinRevisar a un Articulo y actualiza ArticuloProveedor.
    """

    def mapear_articulo(self, articulo_s_revisar_id: Any, articulo_id: Any) -> Dict[str, Any]:
        ArticuloSinRevisar = apps.get_model("articulos", "ArticuloSinRevisar")
        Articulo = apps.get_model("articulos", "Articulo")
        ArticuloProveedor = apps.get_model("articulos", "ArticuloProveedor")

        asr = (
            ArticuloSinRevisar.objects.using("negocio_db").select_related("proveedor", "descuento").get(
                pk=articulo_s_revisar_id
            )
        )
        art = Articulo.objects.using("negocio_db").get(pk=articulo_id)

        # Actualizar todas las relaciones de proveedor que apunten al ASR
        ArticuloProveedor.objects.using("negocio_db").filter(articulo_s_revisar=asr).update(
            articulo=art, articulo_s_revisar=None
        )

        # Consolidar por PrecioDeLista: asegurar un único ArticuloProveedor por cada precio_de_lista
        # Si hay múltiples AP con el mismo precio_de_lista, conservar el primero y eliminar el resto
        from django.db import transaction
        with transaction.atomic(using="negocio_db"):
            dups = (
                ArticuloProveedor.objects.using("negocio_db")
                .values("precio_de_lista")
                .order_by("precio_de_lista")
            )
            seen = set()
            for row in dups:
                pl_id = row["precio_de_lista"]
                if pl_id in seen or pl_id is None:
                    continue
                seen.add(pl_id)
                qs = (
                    ArticuloProveedor.objects.using("negocio_db")
                    .filter(precio_de_lista_id=pl_id)
                    .order_by("id")
                )
                keep = qs.first()
                extra_ids = list(qs.values_list("id", flat=True))[1:]
                if extra_ids:
                    ArticuloProveedor.objects.using("negocio_db").filter(id__in=extra_ids).delete()

        # Marcar ASR como mapeado y fecha (usuario_id eliminado: el campo 'usuario' no es necesario
        # para la importación/mapeo y evita dependencias con auth_user en la base 'default').
        asr.estado = "mapeado"
        asr.fecha_mapeo = timezone.now()
        asr.save(using="negocio_db")

        return {
            "status": "ok",
            "articulo_s_revisar_id": asr.id,
            "articulo_id": art.id,
            "relaciones_actualizadas": True,
        }