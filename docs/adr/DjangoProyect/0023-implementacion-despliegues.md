Architecture Decision Record (ADR): Implementación de Despliegues Automatizados con CI/CD
Adopción de un Pipeline de CI/CD para Despliegues Automáticos en Entornos de Testeo y Producción
Estado
Propuesto (Refinado conjuntamente; pendiente de revisión final antes de implementación).
Contexto
El sistema actual utiliza contenedores gestionados mediante Docker Compose, con despliegues manuales en entornos locales (Raspberry Pi) y potenciales en la nube. El objetivo es automatizar el proceso para que cada release active de forma consistente builds, pruebas y despliegues, reduciendo errores humanos y garantizando separación clara entre entornos de testeo y producción.
Objetivos principales:

Automatizar flujos basados en eventos del repositorio.
Separar estrictamente testeo (staging) y producción.
Manejar errores de manera proactiva con notificaciones y rollback.
Mantener compatibilidad multi-arquitectura y gestión segura de secretos.
Soportar runners heterogéneos: con Docker (stacks completos DRF + Celery + Redis) y sin Docker (desarrollo local en venv o cloud limitado).
Estructura heredable desde el repositorio padre (plantilla) hacia los proyectos hijos, centralizando lógica común y eliminando duplicaciones.

Decisión
Implementar un pipeline CI/CD con GitHub Actions como orquestador principal, organizado en etapas secuenciales: lint/tests → staging/test → gatekeeper → despliegue a producción (solo si staging es exitoso).
El disparador principal será la creación de tags semánticos (ej. vX.Y.Z).
Se prioriza resiliencia mediante dependencias condicionales entre etapas y retroalimentación clara de errores.
La lógica principal del workflow residirá en el repositorio padre para facilitar su reutilización en los proyectos hijos, permitiendo overrides locales mínimos.
Disociación de Versionado y Diseño Heredable Padre-Hijo

Contexto adicional: La plantilla padre y los hijos comparten lógica heredada de versionado (standard-version para changelog, context processor para UI/navbar), pero esto genera acoplamientos residuales (historia compartida en CHANGELOG.md, overwrites en syncs). Para el pipeline CI/CD, el versionado debe ser independiente: padre maneja versiones de plantilla genérica, hijos versiones de negocio específicas.
Decisión:
Disociar versionado: hijos usan changelog propio (sin heredar historia del padre), navbar paramétrico vía .env (APP_VERSION_OVERRIDE o similar, fallback a CHANGELOG hijo). Padre mantiene standard-version para su plantilla, pero hijos desactivan vía toggle (ENABLE_TEMPLATE_VERSIONING=false).
Diseño heredable en templates/base.html:
Navbar: {{NOMBRE_PROYECTO}} v{{VERSION_HIJO}} (parametrizable en .env hijo).
Footer: © 2026 {{NOMBRE_PROYECTO}} v{{VERSION_HIJO}}. Todos los derechos reservados. Este proyecto está basado en DjangoProyects v{{VERSION_PADRE}} (VERSION_PADRE desde constante padre).

En padre: footer redundante pero consistente (“basado en DjangoProyects vX.X.X”).
No sync CHANGELOG.md ni navbar processor entre padre/hijo (gitignore o regla manual).

Beneficios: Independencia en releases de hijos, atribución al padre sin ruido en diffs.
Tradeoffs: Disciplina en syncs (no mergear archivos versionados); mitigado con docs/MIGRACION_HIJOS.md ya implementada.

Pasos conceptuales para la implementación

Estructura del repositorio y ramas
Ramas: develop para features, pre-release para staging, main para producción estable.
Políticas: validación previa a merges; disociación en versionado para evitar overwrites.

Triggers y eventos
Creación de tags semánticos (vX.Y.Z) para activar staging/test.

Etapa de Lint/Tests
Universal, sin Docker.

Etapa de Staging (gatekeeper)
Build in situ, migrate, up con perfiles, smoke/health, rollback si falla.

Gatekeeper Approval
Manual para control humano.

Etapa de Despliegue a Producción
Matrix de runners; in situ si Docker, no-op si no.

Manejo de Secretos y Configuraciones
GitHub secrets por entorno; disociación en versionado para .env hijo-específicos.

Monitoreo y Rollback
Rollback simple: checkout tag anterior + rebuild.

Pruebas e iteración
Validación en hijo con tag de prueba.

Documentación y Mantenimiento


Revisiones periódicas; guía de migración para hijos.

Alternativas consideradas

Triggers automáticos → descartados por riesgo de fallos silenciosos.
Registry remoto → descartados por simplicidad inicial.

Consecuencias

Positivas: Eficiencia, reducción de errores, trazabilidad.
Negativas: Dependencia de GitHub Actions, curva inicial.
Neutrales: Mantenimiento continuo; escalable a más automatización.

Fecha de refinamiento: Enero 19, 2026. Matias