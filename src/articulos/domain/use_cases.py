# Lógica de negocio pura (casos de uso)
"""
Casos de uso del dominio "articulos" siguiendo arquitectura hexagonal.

Estos casos de uso son Python puro y delegan la interacción a puertos
(interfaces) provistos por los adaptadores de infraestructura. No incluyen
dependencias ni lógica específica de Django.
"""

from typing import Any, Dict, List, Optional

from .interfaces import (
    CalcularPrecioPort,
    BuscarArticuloPort,
    MapearArticuloPort,
)


class CalcularPrecioUseCase:
    """
    Caso de uso para calcular precios dinámicos de un artículo.

    Orquesta la operación delegando el cálculo al puerto `CalcularPrecioPort`.
    """

    def __init__(self, precio_repo: CalcularPrecioPort) -> None:
        self._precio_repo = precio_repo

    def execute(
        self,
        articulo_id: Any,
        tipo: str,
        cantidad: int = 1,
        pago_efectivo: bool = False,
    ) -> Dict[str, Any]:
        """
        Delegar el cálculo de precios al repositorio/puerto.
        """
        # Validaciones mínimas y ramas alternativas
        if articulo_id in (None, ""):
            raise ValueError("articulo_id es obligatorio")
        tipo_norm = (tipo or "").strip()
        if not tipo_norm:
            raise ValueError("tipo es obligatorio")
        # Normalizar cantidad: evitar no-positivos
        try:
            cantidad_int = int(cantidad)
        except (TypeError, ValueError):
            cantidad_int = 1
        if cantidad_int <= 0:
            cantidad_int = 1
        resultado = self._precio_repo.calcular_precios(
            articulo_id=articulo_id,
            tipo=tipo_norm,
            cantidad=cantidad_int,
            pago_efectivo=pago_efectivo,
        )
        # Si el repositorio no devuelve datos, retornar estructura vacía
        return resultado or {}


class BuscarArticuloUseCase:
    """
    Caso de uso para buscar artículos por código y/o abreviatura.

    Delegará la consulta al puerto `BuscarArticuloPort`.
    """

    def __init__(self, busqueda_repo: BuscarArticuloPort) -> None:
        self._busqueda_repo = busqueda_repo

    def execute(self, query: str, abreviatura: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Delegar la búsqueda al repositorio/puerto.
        """
        q = (query or "").strip()
        # Rama de retorno cuando no hay datos de entrada
        if not q and not abreviatura:
            return []
        resultado = self._busqueda_repo.buscar_articulos(query=q, abreviatura=abreviatura)
        # Rama alternativa si el repositorio devuelve vacío
        return resultado or []


class MapearArticuloUseCase:
    """
    Caso de uso para mapear/consolidar un ArticuloSinRevisar hacia un Articulo.

    Delegará la operación al puerto `MapearArticuloPort`.
    """

    def __init__(self, mapeo_repo: MapearArticuloPort) -> None:
        self._mapeo_repo = mapeo_repo

    def execute(self, articulo_s_revisar_id: Any, articulo_id: Any, usuario_id: Any) -> Dict[str, Any]:
        """
        Delegar el mapeo al repositorio/puerto.
        """
        # Validaciones mínimas
        if articulo_s_revisar_id in (None, ""):
            raise ValueError("articulo_s_revisar_id es obligatorio")
        if articulo_id in (None, ""):
            raise ValueError("articulo_id es obligatorio")
        if usuario_id in (None, ""):
            raise ValueError("usuario_id es obligatorio")
        resultado = self._mapeo_repo.mapear_articulo(
            articulo_s_revisar_id=articulo_s_revisar_id,
            articulo_id=articulo_id,
            usuario_id=usuario_id,
        )
        return resultado or {}