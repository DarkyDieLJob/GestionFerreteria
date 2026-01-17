# Nombre del Proyecto

Breve descripción del proyecto. Este repositorio se generó a partir de la plantilla DjangoProyects.

## Documentación de la plantilla

- Guía completa de DjangoProyects: ver [docs/DJANGOPROYECTS.md](docs/DJANGOPROYECTS.md).
- Instalación y comandos rápidos: ver [docs/INSTALACION.md](docs/INSTALACION.md).

### Persistencia en producción

Este template adopta una carpeta `persist/` por host para centralizar secretos, media, data y logs mediante bind mounts controlados por `HOST_PERSIST` (default `.` en desarrollo).
Consulta detalles y pasos en:
- [docs/DJANGOPROYECTS.md](docs/DJANGOPROYECTS.md#patrón-de-persistencia-centralizada-persist)
- [docs/INSTALACION.md](docs/INSTALACION.md)
