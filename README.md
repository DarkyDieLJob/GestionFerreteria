# Gestión Ferretería

Plataforma Django orientada a centralizar inventario, proveedores y listas de precios de una ferretería. El código vive en `src/` y sigue arquitectura hexagonal con apps desacopladas.

## Documentación

- **Guía de instalación**: [`docs/INSTALACION.md`](docs/INSTALACION.md)
- **Estructura del proyecto**: [`docs/ESTRUCTURA.md`](docs/ESTRUCTURA.md)
- **Flujo de trabajo Git**: [`docs/GIT_AGENTES.md`](docs/GIT_AGENTES.md)
- **Lineamientos para agentes automáticos**: [`docs/PAUTAS_AGENTES.md`](docs/PAUTAS_AGENTES.md)
- **Notas sobre proyectos Django**: [`docs/DJANGOPROYECTS.md`](docs/DJANGOPROYECTS.md)
- **Decisiones de arquitectura (ADR)**:
  - [`docs/adr/0001-adopcion-arquitectura-hexagonal.md`](docs/adr/0001-adopcion-arquitectura-hexagonal.md)
  - [`docs/adr/0002-adopcion-github-template-repository.md`](docs/adr/0002-adopcion-github-template-repository.md)

## Primeros pasos

1. Clona el repositorio y crea un entorno virtual.
2. Sigue la guía de [`docs/INSTALACION.md`](docs/INSTALACION.md) para instalar dependencias desde `requirements/` y preparar `src/.env`.
3. Ejecuta comandos de Django desde `src/`, p. ej. `python manage.py migrate` y `python manage.py runserver`.

## Estado operativo

- La organización de entornos, pipelines y roles se detalla en [`docs/DJANGOPROYECTS.md`](docs/DJANGOPROYECTS.md).
- El estado de ADR específicos se mantiene en `docs/adr/`.
