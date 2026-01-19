###############################
# Builder de Python (multi-arch)
###############################
ARG PYTHON_VERSION=3.11
ARG TARGETPLATFORM
ARG TARGETARCH
ARG TARGETOS
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-slim-bookworm AS py-builder

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

# Copiar solo lo necesario para construir Tailwind (si existe)
COPY frontend/ ./frontend/
COPY static/ ./static/

WORKDIR /app/frontend
RUN --mount=type=cache,target=/root/.npm \
    npm ci || npm install \
    && npm run build

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

# Entrypoint
COPY scripts/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]

########################################
# Runtime con frontend (copia estáticos)
########################################
FROM runtime AS runtime-frontend

# Nota: este stage solo copia artefactos estáticos construidos por Node.
# No incluye Node/npm en la imagen final.
COPY --from=node-builder /app/static/css /app/static/css
