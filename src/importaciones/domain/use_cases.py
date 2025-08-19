# Lógica de negocio pura (casos de uso)
"""
Caso de uso del dominio "importaciones" siguiendo arquitectura hexagonal.

Este caso de uso es Python puro y delega la interacción a un puerto
(interface) provisto por un adaptador de infraestructura. No incluye
dependencias ni lógica específica de Django.
"""

from typing import Any, Dict, List, Tuple

from ..ports.interfaces import ImportarExcelPort


class ImportarExcelPort:  # hint-only interface (no implementación)
    """Puerto esperado para procesar y previsualizar archivos Excel."""

    def procesar_excel(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError

    def vista_previa_excel(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError

    def listar_hojas_excel(self, nombre_archivo: str) -> List[str]:  # pragma: no cover - interface
        raise NotImplementedError

    def generar_csvs_por_hoja(
        self,
        proveedor_id: Any,
        nombre_archivo: str,
        selecciones: Dict[str, Dict[str, int]],
    ) -> List[Tuple[str, str]]:  # pragma: no cover - interface
        raise NotImplementedError

    def procesar_pendientes(self) -> Dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError


class ImportarExcelUseCase:
    """
    Caso de uso para importar listas de precios/stock desde un archivo Excel.

    - `procesar(...)` delega al puerto para ejecutar la importación completa.
    - `vista_previa(...)` delega al puerto para obtener una previsualización
      de lo que se importaría (validaciones, filas, mapeos, etc.).
    - `listar_hojas(...)` lista hojas de un archivo Excel subido.
    - `generar_csvs_por_hoja(...)` genera CSVs y agenda pendientes por hoja.
    - `agendar_pendientes()` procesa la cola de pendientes.
    """

    def __init__(self, excel_repo: "ImportarExcelPort") -> None:
        self._excel_repo = excel_repo

    def procesar(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:
        """Delegar el procesamiento del Excel al repositorio/puerto."""
        return self._excel_repo.procesar_excel(proveedor_id=proveedor_id, nombre_archivo=nombre_archivo)

    def vista_previa(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:
        """Delegar la vista previa del Excel al repositorio/puerto."""
        return self._excel_repo.vista_previa_excel(proveedor_id=proveedor_id, nombre_archivo=nombre_archivo)

    # Nuevo flujo multi-hoja
    def listar_hojas(self, nombre_archivo: str) -> List[str]:
        """Lista las hojas disponibles en el archivo Excel subido."""
        return self._excel_repo.listar_hojas_excel(nombre_archivo=nombre_archivo)

    def generar_csvs_por_hoja(
        self,
        proveedor_id: Any,
        nombre_archivo: str,
        selecciones: Dict[str, Dict[str, int]],
    ) -> List[Tuple[str, str]]:
        """
        Genera CSVs por hoja y agenda entradas en ArchivoPendiente.
        `selecciones` es un dict: hoja -> { 'config_id': int, 'start_row': int }.
        """
        return self._excel_repo.generar_csvs_por_hoja(
            proveedor_id=proveedor_id,
            nombre_archivo=nombre_archivo,
            selecciones=selecciones,
        )

    def agendar_pendientes(self) -> Dict[str, Any]:
        """Procesa los `ArchivoPendiente` en cola y devuelve estadísticas."""
        return self._excel_repo.procesar_pendientes()