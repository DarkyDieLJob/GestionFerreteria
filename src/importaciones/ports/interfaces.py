# Interfaces para el dominio
"""
Definiciones de puertos del dominio de importaciones (Python puro).
No depende de Django ni de infraestructura.
"""

from typing import Any, Dict, List, Tuple


class ImportarExcelPort:  # pragma: no cover - interfaz
    """Puerto esperado para procesar y previsualizar archivos Excel.

    Los adaptadores (por ejemplo, repository basado en Django) implementarán
    estos métodos.
    """

    def procesar_excel(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:
        raise NotImplementedError

    def vista_previa_excel(self, proveedor_id: Any, nombre_archivo: str) -> Dict[str, Any]:
        raise NotImplementedError

    def listar_hojas_excel(self, nombre_archivo: str) -> List[str]:
        raise NotImplementedError

    def generar_csvs_por_hoja(
        self,
        proveedor_id: Any,
        nombre_archivo: str,
        selecciones: Dict[str, Dict[str, int]],
    ) -> List[Tuple[str, str]]:
        raise NotImplementedError

    def procesar_pendientes(self) -> Dict[str, Any]:
        raise NotImplementedError