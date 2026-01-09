# Colas de tareas (Celery + Redis)

Esta guía documenta la funcionalidad de procesamiento en background basada en Celery (worker) y Redis (broker), ya integrada en el proyecto y el despliegue con Docker Compose.

## Objetivo

- Desacoplar tareas pesadas o de larga duración del request HTTP.
- Procesar importaciones de planillas de precio (CSV/Excel) sin bloquear la UI.
- Mantener la lógica de negocio central en los casos de uso/repositorios existentes.

## Componentes

- Redis (broker): encola y distribuye tareas.
- Celery worker: ejecuta las tareas.
- Django web (Gunicorn): expone la app y dispara tareas según sea necesario.

Los servicios están definidos en `docker-compose.yml`:
- `redis`: broker de mensajes (sin exposición de puertos hacia el host).
- `worker`: Celery ejecutando con `-A core_config`.
- `app`: servicio web (Gunicorn) con `--chdir src`.

## Configuración

Variables relevantes (definidas en `docker-compose.yml` o `src/.env`):

- `CELERY_BROKER_URL=redis://redis:6379/0`
- `CELERY_TIMEZONE=UTC` (ajustable)
- (Opcional) `CELERY_RESULT_BACKEND=redis://redis:6379/1` para registrar resultados de tareas.

El archivo `src/core_config/celery.py` inicializa la app de Celery y autodetecta tareas (`app.autodiscover_tasks()`).

## Tareas incluidas

- `importaciones.procesar_pendientes` (`src/importaciones/tasks.py`):
  - Reutiliza `ExcelRepository.procesar_pendientes()`.
  - Recorre `ArchivoPendiente(procesado=False)`, procesa cada CSV, upsert de `PrecioDeLista`, sincroniza entidades relacionadas y marca `procesado=True`.

## Comandos útiles

- Ver estado de servicios:
  - `docker compose ps`
  - `docker compose logs -f worker`

- Disparar procesamiento de pendientes vía Celery:
  - `docker compose exec worker celery -A core_config call importaciones.procesar_pendientes`
  - Devuelve un UUID de tarea. Para ver resultados (si se configuró backend):
    - `docker compose exec worker celery -A core_config result <TASK_ID>`

- Alternativa síncrona (sin Celery):
  - `docker compose exec app python src/manage.py procesar_pendientes_script`
  - Opcional: `--limit 5`.

## Ajustes de rendimiento (RPi 4 sugerido)

- Worker Celery: `--concurrency=1` o `2` como máximo.
- Gunicorn: `--workers 1..2`, `--timeout 60`.
- Redis como solo broker (sin persistencia AOF/RDB) para reducir IO.

## Seguridad y operación

- No exponer puertos de Redis/Postgres fuera de la red interna de Docker.
- Secretos en `src/.env` (no commitear). Ajustar `SECRET_KEY`, `POSTGRES_PASSWORD`, etc.
- Backups: si usás Postgres, programar `pg_dump` periódico (ver guía de backups si aplica).

## Integración con la UI

Actualmente, el flujo de importación en `http://<host>:8001/importaciones/` encola archivos convertidos a CSV (`ArchivoPendiente`). El procesamiento se dispara manualmente (Celery o management command). La vista de confirmación muestra la cola de pendientes no procesados.

## Próximamente

- “Vista visualizadora de tareas”: se planifica una app de Django dedicada para visualizar tareas encoladas, activas y finalizadas (historial), con filtros por estado/fecha y reintentos. Se evaluarán opciones como:
  - Implementación propia (modelo ligero con auditoría de tareas).
  - Integración con paneles externos (Flower) según restricciones del entorno.

---

Última actualización: ver `CHANGELOG.md` y los commits relacionados a Docker/Celery/Redis.
