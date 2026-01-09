# Documentación del proyecto

Bienvenido a la documentación central del proyecto. Usa este índice para navegar los distintos apartados.

## Índice

- Guía de la plantilla base
  - DJANGOPROYECTS: guía completa de la plantilla
    - docs/DJANGOPROYECTS.md
  - Instalación y comandos rápidos
    - docs/INSTALACION.md
  - Estructura y arquitectura
    - docs/ESTRUCTURA.md

- Flujo de trabajo y pautas
  - Git: flujo de ramas, PRs, releases
    - docs/GIT_AGENTES.md
  - Pautas operativas para agentes
    - docs/PAUTAS_AGENTES.md

- Funcionalidades del sistema
  - Colas de tareas (Celery + Redis)
    - docs/COLAS_TAREAS.md

- ADRs (decisiones de arquitectura)
  - docs/adr/GestionFerreteria/

## Operación (placeholders)

- Healthchecks (TODO):
  - Definir healthchecks en docker-compose para `db`, `redis`, `app`, `worker`.
  - Establecer `depends_on` por salud y tiempos de espera adecuados.
- Backups (TODO):
  - Crear contenedor/cron de `pg_dump` con retención y restauración documentada.
  - Política de rotación y ubicación de backups en el host/SSD.
- Monitoreo de tareas (TODO):
  - Evaluar Flower u otra herramienta para entorno local.
  - Alternativa: vista interna de Django (ver sección siguiente).

## Visualizador de tareas (placeholders)

- App Django dedicada (TODO):
  - Listado de tareas: encoladas, activas, finalizadas (con filtros por estado/fecha).
  - Reintentos y reprogramación manual.
  - Auditoría mínima (timestamps, actor que disparó, parámetros relevantes).
  - Permisos: restringir a staff.

## Notas

- Si agregas nueva documentación, enlázala aquí para mantener la navegación unificada.
- “Próximamente”: vista visualizadora de tareas (app Django dedicada) para monitoreo de tareas encoladas/activas/finalizadas.
