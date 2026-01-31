###############################
# Builder de Python (wheels)
###############################
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bookworm AS py-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libffi-dev \
       libssl-dev \
       libpq-dev \
       cargo \
       rustc \
       git \
       curl \
       sqlite3 \
       libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache de dependencias Python como wheels
COPY requirements/ ./requirements/
RUN python -m pip install --upgrade pip \
    && python -m pip wheel --wheel-dir=/wheels -r requirements/runtime.txt

###############################
# Builder de Node (opcional)
###############################
FROM node:20-alpine AS node-builder
WORKDIR /app

# Asegurar que el directorio de estáticos exista aunque no haya carpeta static/ en el repo
RUN mkdir -p /app/static/css

WORKDIR /app/frontend
RUN --mount=type=cache,target=/root/.npm \
    if [ -f package.json ]; then \
      (npm ci || npm install) && (npm run build || true); \
    else \
      echo "No frontend/package.json found; skipping frontend build"; \
    fi

###############################
# Runtime base sin Node/npm
###############################
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       sqlite3 \
       libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias desde wheels (no requiere toolchain aquí)
COPY --from=py-builder /wheels /wheels
COPY requirements/ ./requirements/
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-index --find-links=/wheels -r requirements/runtime.txt

# Copiar la aplicación
COPY . .
RUN mkdir -p /app/src/data

# Copiar entrypoint
COPY scripts/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copiar artefactos estáticos construidos por node-builder (si existen)
COPY --from=node-builder /app/static/css /app/static/css

# Exponer puerto de la app (se mantiene 8001)
EXPOSE 8001

# Mantener comando/entrypoint del hijo para compatibilidad
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8001"]
