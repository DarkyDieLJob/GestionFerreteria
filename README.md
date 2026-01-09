# Nombre del Proyecto

Breve descripción del proyecto. Este repositorio se generó a partir de la plantilla DjangoProyects.

## Documentación de la plantilla

- Guía completa de DjangoProyects: ver [docs/DJANGOPROYECTS.md](docs/DJANGOPROYECTS.md).
- Instalación y comandos rápidos: ver [docs/INSTALACION.md](docs/INSTALACION.md).
- Índice general de documentación: ver [docs/README.md](docs/README.md).
- Colas de tareas (Celery + Redis): ver [docs/COLAS_TAREAS.md](docs/COLAS_TAREAS.md).

## Colas de tareas (Celery + Redis)

- Nueva funcionalidad de procesamiento en background documentada en [docs/COLAS_TAREAS.md](docs/COLAS_TAREAS.md).
- Incluye worker Celery, broker Redis y tarea para procesar pendientes de importaciones.
- Próximamente: vista visualizadora de tareas (app Django dedicada) para monitoreo de encoladas/activas/finalizadas.

## Primeros pasos

1. Copia `src/.env.example` a `src/.env` y ajusta las variables.
2. Crea y activa un entorno virtual, instala dependencias y migra la base de datos.
3. Ejecuta el servidor de desarrollo con `python ./src/manage.py runserver`.

Para lineamientos de trabajo y git flow, consulta [docs/PAUTAS_AGENTES.md](docs/PAUTAS_AGENTES.md) y [docs/GIT_AGENTES.md](docs/GIT_AGENTES.md).
