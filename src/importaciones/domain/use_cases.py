# Lógica de negocio pura (casos de uso)
"""
Caso de uso del dominio "importaciones" siguiendo arquitectura hexagonal.

Este caso de uso es Python puro y delega la interacción a un puerto
(interface) provisto por un adaptador de infraestructura. No incluye
dependencias ni lógica específica de Django.
"""

from typing import Any, Dict


class ImportarExcelPort:  # hint-only interface (no implementación)
    """Puerto esperado para procesar y previsualizar archivos Excel."""

    def procesar_excel(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError

    def vista_previa_excel(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError


class ImportarExcelUseCase:
    """
    Caso de uso para importar listas de precios/stock desde un archivo Excel.

    - `procesar(...)` delega al puerto para ejecutar la importación completa.
    - `vista_previa(...)` delega al puerto para obtener una previsualización
      de lo que se importaría (validaciones, filas, mapeos, etc.).
    """

    def __init__(self, excel_repo: "ImportarExcelPort") -> None:
        self._excel_repo = excel_repo

    def procesar(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:
        """Delegar el procesamiento del Excel al repositorio/puerto."""
        return self._excel_repo.procesar_excel(proveedor_id=proveedor_id, nombre_archivo=nombre_archivo)

    def vista_previa(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:
        """Delegar la vista previa del Excel al repositorio/puerto."""
        return self._excel_repo.vista_previa_excel(proveedor_id=proveedor_id, nombre_archivo=nombre_archivo)