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

        PrecioDeLista = apps.get_model("precios", "PrecioDeLista")
        ArticuloSinRevisar = apps.get_model("articulos", "ArticuloSinRevisar")
        ArticuloProveedor = apps.get_model("articulos", "ArticuloProveedor")

        results: List[Dict[str, Any]] = []

        # PrecioDeLista: match exacto del código normalizado y opcionalmente abreviatura por proveedor
        qs_pl: QuerySet = PrecioDeLista.objects.using("negocio_db").select_related("proveedor").filter(codigo=code)
        if abbr:
            qs_pl = qs_pl.filter(proveedor__abreviatura__iexact=abbr)
        for pl in qs_pl[:50]:
            results.append(
                {
                    "tipo": "precio_lista",
                    "id": pl.id,
                    "codigo": getattr(pl, "get_codigo_completo", lambda: f"{pl.codigo}{pl.proveedor.abreviatura}")(),
                    "descripcion": pl.descripcion,
                    "proveedor": pl.proveedor.abreviatura,
                    "precio": float(pl.precio),
                }
            )

        # ArticuloProveedor: buscar por codigo_proveedor y abreviatura
        base_no_slash = code.rstrip("/")
        qs_ap: QuerySet = ArticuloProveedor.objects.using("negocio_db").select_related(
            "proveedor", "precio_de_lista", "articulo"
        )
        qs_ap = qs_ap.filter(codigo_proveedor=base_no_slash)
        if abbr:
            qs_ap = qs_ap.filter(proveedor__abreviatura__iexact=abbr)
        for ap in qs_ap[:50]:
            codigo = getattr(ap, "get_codigo_completo", lambda: f"{ap.codigo_proveedor}/{ap.proveedor.abreviatura}")()
            results.append(
                {
                    "tipo": "articulo_proveedor",
                    "id": ap.id,
                    "codigo": codigo,
                    "descripcion": ap.descripcion_proveedor,
                    "proveedor": ap.proveedor.abreviatura,
                    "precio": float(ap.precio),
                }
            )

        # ArticuloSinRevisar: buscar por codigo_proveedor y abreviatura
        qs_asr: QuerySet = ArticuloSinRevisar.objects.using("negocio_db").select_related("proveedor")
        qs_asr = qs_asr.filter(codigo_proveedor=base_no_slash)
        if abbr:
            qs_asr = qs_asr.filter(proveedor__abreviatura__iexact=abbr)
        for asr in qs_asr[:50]:
            results.append(
                {
                    "tipo": "articulo_sin_revisar",
                    "id": asr.id,
                    "codigo": f"{asr.codigo_proveedor}/{asr.proveedor.abreviatura}",
                    "descripcion": asr.descripcion_proveedor,
                    "proveedor": asr.proveedor.abreviatura,
                    "precio": float(asr.precio),
                }
            )

        return results


class MapeoRepository(MapearArticuloPort):
    """
    Implementación del puerto `MapearArticuloPort` usando Django ORM.

    Mapea un ArticuloSinRevisar a un Articulo y actualiza ArticuloProveedor.
    """

    def mapear_articulo(self, articulo_s_revisar_id: Any, articulo_id: Any, usuario_id: Any) -> Dict[str, Any]:
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

        # Marcar ASR como mapeado, usuario y fecha
        asr.estado = "mapeado"
        asr.fecha_mapeo = timezone.now()
        try:
            # asignación directa al FK por id, evitando cargar auth.User
            asr.usuario_id = int(usuario_id) if usuario_id is not None else None
        except Exception:
            asr.usuario_id = usuario_id
        asr.save(using="negocio_db")

        return {
            "status": "ok",
            "articulo_s_revisar_id": asr.id,
            "articulo_id": art.id,
            "relaciones_actualizadas": True,
        }