# Architecture Decision Record (ADR): Módulo opcional de análisis histórico y visualización de ventas en GestionFerreteria, basado en datos legacy de Ferreteria_v3

## Estado
Propuesto

## Contexto
Ferreteria_v3 está en producción con funcionalidad operativa consolidada (búsqueda, actualización, facturación), pero con arquitectura desorganizada y estructuras de tablas no compatibles con GestionFerreteria.

GestionFerreteria, en desarrollo, sigue patrones del repositorio padre DjangoProyects (arquitectura hexagonal, configuraciones modulares, toggles) y actualmente implementa búsqueda y carga/actualización de artículos, con pendientes como carrito y facturación.

Se busca incorporar un módulo de visualizaciones históricas (diagramas por artículo, proveedor y combinaciones temporales) directamente en GestionFerreteria, consumiendo inicialmente datos de Ferreteria_v3 mediante copia estática de db.sqlite3.

La arquitectura hexagonal de GestionFerreteria permite manejar la disparidad de tablas mediante un adaptador legacy temporal, facilitando la futura migración a la estructura nativa del proyecto sin impactar la lógica de agregación ni visualización.

En vez de crear un proyecto separado o una app aislada desde cero, se desarrollará el módulo en una rama dedicada a partir de develop, integrando los cambios de forma incremental y aprovechando el pipeline CI/CD existente.

## Decisión
Desarrollar el módulo de análisis histórico y visualización de ventas como conjunto de cambios en una rama nueva derivada de develop dentro del repositorio GestionFerreteria.

Características clave:

- Rama dedicada (ej. feature/analisis-historico-legacy) para aislamiento durante el desarrollo.
- Activación controlada por toggle env (ENABLE_ANALISIS_HISTORICO=true).
- Fuente inicial: copia de db.sqlite3 de Ferreteria_v3 en media/, con adaptador que abstraiga disparidades de tablas.
- Arquitectura hexagonal preservada: puerto para consultas agregadas + adaptador legacy temporal.
- Integración progresiva: vistas, urls, templates y validaciones condicionales que no afectan el núcleo si el toggle está desactivado.
- Despliegue unificado: mismo pipeline, mismas imágenes Docker, mismas validaciones staging → producción.

## Pasos a Seguir para la Implementación

### Creación de la rama de desarrollo
- Crear rama feature/analisis-historico-legacy (o similar) a partir de develop.
- Mantener commits atómicos y descriptivos para facilitar revisión y merge.

### Configuración de la fuente legacy
- Agregar entrada en DATABASES para la base legacy en media/db.sqlite3.
- Implementar adaptador que mapee estructuras no compatibles (joins alternativos, campos equivalentes).
- Validar existencia e integridad del archivo al inicio (warning + desactivación graceful si falla).

### Desarrollo incremental del módulo
- Puerto para agregaciones históricas (por período, artículo, proveedor, combinaciones).
- Vistas y plantillas para generar y servir diagramas (renderizado server-side inicial).
- Controles de filtro y período en interfaz, visibles solo si habilitado.

### Ajustes condicionales en el pipeline
- Agregar checks en staging: si toggle activado → validar archivo legacy + ejecución de consultas de prueba.
- Mantener gatekeeper completo para el proyecto, con skip condicional del módulo.

### Estrategia de evolución
- Documentar el adaptador legacy como transitorio.
- Prever reemplazo por: consultas nativas de GestionFerreteria (post-facturación) o base histórica unificada tras migración de datos legacy.
- Merge progresivo a develop una vez validado en staging.

## Alternativas Consideradas
- Rama larga sin merge progresivo → Descartada por riesgo de divergencia y dificultad de integración final.
- Proyecto hijo separado → Descartado por duplicación de mantenimiento y pipeline.
- App completamente aislada sin toggle → Descartada para no forzar consumo en instalaciones que no lo necesiten.

## Consecuencias

### Positivas
- Desarrollo aislado pero integrado en el mismo repositorio.
- Aprovechamiento directo del CI/CD y runners existentes.
- Camino claro hacia reemplazo del adaptador legacy gracias a la hexagonal.

### Negativas
- Dependencia inicial de copia manual legacy.
- Complejidad temporal en el adaptador para mapear disparidades.

### Neutrales
- Requiere merge cuidadoso a develop cuando el módulo esté estable.
- Escalabilidad futura depende de completar migración de datos y funcionalidades pendientes.
