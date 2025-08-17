"""
Puertos (Interfaces) para la arquitectura hexagonal del contexto "articulos".

Estas interfaces definen contratos puros de Python (sin dependencias de Django)
que serán implementados por adaptadores/repositorios en la capa de infraestructura.
"""

from typing import Any, Dict, List, Optional, Union


class CalcularPrecioPort:
    """
    Puerto para cálculo de precios dinámicos de artículos.

    Responsabilidad:
    - Dado un identificador de artículo y parámetros de cálculo, retorna
      los precios calculados.

    Debe soportar artículos existentes (Articulo) y sin revisar (ArticuloSinRevisar).
    """

    def calcular_precios(
        self,
        articulo_id: Union[int, str],
        tipo: str,
        cantidad: int,
        pago_efectivo: bool,
    ) -> Dict[str, Any]:
        """
        Calcula precios dinámicos para un artículo.

        Parametros:
        - articulo_id: Identificador del artículo objetivo (puede ser numérico o string según implementación).
        - tipo: Tipo de artículo a calcular (por ejemplo: "articulo" o "sin_revisar").
        - cantidad: Cantidad solicitada para el cálculo (influye en precio por bulto, etc.).
        - pago_efectivo: Indica si se aplica el esquema de efectivo.

        Retorna:
        - Diccionario con las claves esperadas:
          {
            "base": float,
            "final": float,
            "final_efectivo": float,
            "bulto": float,
            "final_bulto": float,
            "final_bulto_efectivo": float
          }

        Debe lanzar NotImplementedError en la interfaz.
        """
        raise NotImplementedError


class BuscarArticuloPort:
    """
    Puerto para búsqueda de artículos por código y abreviatura.

    Debe poder consultar códigos con o sin abreviatura (ej.: "37", "37/Vj")
    en orígenes como PrecioDeLista, ArticuloSinRevisar y ArticuloProveedor.
    """

    def buscar_articulos(
        self,
        query: str,
        abreviatura: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca artículos por código (y opcionalmente abreviatura).

        Parametros:
        - query: Cadena de búsqueda principal (código base o completo).
        - abreviatura: Abreviatura de proveedor (opcional) para restringir búsqueda.

        Retorna:
        - Lista de resultados en forma de dicts con la información mínima necesaria
          (p. ej. {"id": Any, "tipo": str, "codigo": str, "descripcion": str, ...}).

        Debe lanzar NotImplementedError en la interfaz.
        """
        raise NotImplementedError


class MapearArticuloPort:
    """
    Puerto para mapear/consolidar un ArticuloSinRevisar hacia un Articulo existente.

    La operación debe actualizar las relaciones correspondientes (p. ej. ArticuloProveedor)
    según la implementación concreta del adaptador.
    """

    def mapear_articulo(
        self,
        articulo_s_revisar_id: Union[int, str],
        articulo_id: Union[int, str],
        usuario_id: Union[int, str],
    ) -> Dict[str, Any]:
        """
        Mapea un ArticuloSinRevisar hacia un Articulo.

        Parametros:
        - articulo_s_revisar_id: Identificador del ArticuloSinRevisar a consolidar.
        - articulo_id: Identificador del Articulo destino.
        - usuario_id: Identificador del usuario que realiza la acción (auditoría).

        Retorna:
        - Información del mapeo realizado (por ejemplo estado, ids resultantes, etc.).

        Debe lanzar NotImplementedError en la interfaz.
        """
        raise NotImplementedError
