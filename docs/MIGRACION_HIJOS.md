# Guía rápida de migración y adopción desde la plantilla padre (prioridades 1–4)

Esta guía resume los cambios clave aplicados en el padre y los pasos para adoptarlos en proyectos hijos (GestionFerreteria, GestionGastronomica, GestionTeatroBar, etc.). Recomendación: valida primero en local o staging; luego aplica en producción.

## Pasos generales (previos)
- Actualiza el hijo desde el padre (merge o rebase):
  - `git fetch` del padre y mergea los cambios en tu rama del hijo.
  - Resuelve conflictos (especial atención a: `.gitignore`, `docker-compose.yml`, `Dockerfile`, `scripts/docker-entrypoint.sh`, `src/core_config/settings.py`).
- Prepara persistencia en el host (si no existe):
  - Crea `persist/` con subcarpetas: `env/`, `media/`, `data/`, `logs/`.
  - Revisa permisos/propiedad para el usuario que ejecuta Docker/runner.
- Variables de entorno:
  - Mueve el `.env` del proyecto a `persist/env/.env`.
  - Usa `src/.env.example` (padre) para ajustar toggles y parámetros.

## Checklist por prioridad

### 1) Persistencia centralizada
- Montajes estándar controlados por `HOST_PERSIST` (default `.`):
  - `persist/env/.env` → `/app/src/.env` (RO)
  - `persist/media` → `/app/src/media`
  - `persist/data` → `/app/src/data`
  - `persist/logs` → `/app/logs`
- Verifica que `docker-compose.yml` del hijo use estos montajes.

### 1.5) Healthchecks y migraciones controladas
- Ejecuta migraciones ANTES del `up` para evitar condiciones de carrera:
  - `python project_manage.py migrate`
- Levanta servicios:
  - `make up` (base) o `PROFILE=db,broker,worker make up`
- Verifica health:
  - `python project_manage.py status` o `docker compose ps` (espera `healthy`).

### 1.9) .gitignore robusto
- Alinea `.gitignore` del hijo con el del padre:
  - Ignorar `persist/**`, `node_modules/`, `src/staticfiles/`, `src/media/`, `__pycache__/`, caches de herramientas, etc.
  - Migraciones: ignora `src/**/migrations/*.py` salvo `__init__.py`, a menos que el hijo decida versionarlas.

### 2) Entrypoint condicional + Dockerfile multi-arch/multi-stage
- Builds:
  - Sin frontend: `docker buildx build --target runtime ...`
  - Con frontend: `docker buildx build --target runtime-frontend ...`
- Flags de runtime en entrypoint:
  - `NO_FRONTEND=true` para omitir pasos de Tailwind en runtime.
  - `ENABLE_COLLECTSTATIC=true` si necesitas recolectar estáticos al arrancar.
  - `RUN_MAKEMIGRATIONS=false` si quieres desactivar `makemigrations` en entrypoint.

### 3A) CLI genérico + Makefile
- Usa los atajos:
  - `make up`, `make down`, `make logs`, `make status`, `make migrate`
  - Avanzado: `python project_manage.py compose -- <args>`

### 3B) Perfiles en docker compose
- Activa solo lo necesario:
  - App + DB: `--profile db`
  - App + DB + Broker: `--profile db --profile broker`
  - + Worker: `--profile worker`
- Con CLI/Makefile:
  - `PROFILE=db,broker,worker make up`
  - `python project_manage.py up --profile db,broker,worker`

### 4) Settings modulares + README modular
- Ajusta toggles en `persist/env/.env`:
  - `USE_POSTGRES=true|false`, `CELERY_ENABLED=true|false`, `WHITENOISE_ENABLED=`, `ALLAUTH_ENABLED=true|false`, `ALLAUTH_PROVIDERS=github,google`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DEBUG_INFO=false`.
- Mantén el `README.md` del hijo específico y alineado al producto.
  - No mergees el `README.md` del padre en el hijo.
  - Puedes tomar `docs/README_HIJOS_TEMPLATE.md` (padre) como base.

## Verificación post-migración
- `python project_manage.py status` o `docker compose ps` → servicios `healthy`.
- `FOLLOW=1 SERVICES=app,worker make logs` → sin errores.
- Acceso a la aplicación (HTTP) funcionando.
- Si aplica: tareas Celery operando con perfiles `broker,worker`.

## Recomendaciones finales
- Commits claros en el hijo, documentando decisiones (ej. perfiles activos, toggles).
- Crea un tag/release del hijo tras validar en staging/producción.
- Si surge conflicto en archivos clave (compose, settings, Dockerfile/entrypoint), resuélvelo manualmente y commitea el override en el hijo.
- Mantén referencia a `docs/DJANGOPROYECTS.md` (padre) para operación cotidiana.
