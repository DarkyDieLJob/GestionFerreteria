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
        return self._precio_repo.calcular_precios(
            articulo_id=articulo_id,
            tipo=tipo,
            cantidad=cantidad,
            pago_efectivo=pago_efectivo,
        )


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
        return self._busqueda_repo.buscar_articulos(query=query, abreviatura=abreviatura)


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
        return self._mapeo_repo.mapear_articulo(
            articulo_s_revisar_id=articulo_s_revisar_id,
            articulo_id=articulo_id,
            usuario_id=usuario_id,
        )