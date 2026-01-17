# Receta: Despliegue seguro con healthchecks + migraciones controladas

## Preparación
- Exporta `HOST_PERSIST` y asegúrate de la estructura `persist/` en el host.
- Ajusta `persist/env/.env` (permisos 640, propietario UID/GID del runner).
- Activa perfiles según tu entorno: `db`, `broker` (redis), `worker`.

## Build/Pull
```bash
# Construcción local (no hay registry remoto)
docker compose build
# Si usas imágenes preconstruidas en tu contexto, podrías hacer pull (opcional)
# docker compose pull
```

## Migraciones (previas al up -d)
```bash
docker compose run --rm app python src/manage.py migrate
```

## Arranque (ordenado por healthchecks)
```bash
docker compose up -d [--profile db] [--profile broker] [--profile worker]
```

## Verificación
- `docker compose ps` (espera `healthy` en servicios críticos: db, redis, app, worker si aplica).
- `docker compose logs --no-log-prefix --since=2m` (revisar errores recientes).
- (Si se agrega a futuro) endpoint `/health/` responde 200.

## Notas
- Healthchecks:
  - db: `pg_isready`
  - redis: `redis-cli ping`
  - app: `python src/manage.py check --deploy` (placeholder minimalista)
  - worker: `python src/manage.py check`
- depends_on con `condition: service_healthy` asegura orden de arranque y tolerancia a latencia.
- Tradeoff: pequeño tiempo extra (migrate + healthchecks) a cambio de mayor estabilidad.

## Rollback simple
1. `docker compose down`
2. Restaurar snapshot de `persist/` (ver guía en docs/INSTALACION.md)
3. `docker compose up -d`
