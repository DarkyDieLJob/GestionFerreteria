##### Desde plantilla padre (prioridad 4): multi-stage con target 'runtime'

## Stage builder: instala dependencias en un venv y construye frontend en build-time
FROM python:3.11-slim-bookworm AS builder

# Evitar creación de .pyc y mejorar logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependencias de compilación y utilidades (incluye Node/npm SOLO en builder)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libffi-dev \
       libssl-dev \
       cargo \
       rustc \
       git \
       curl \
       sqlite3 \
       libsqlite3-dev \
       nodejs \
       npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar únicamente requirements para cacheo eficiente (Python)
COPY requirements/ ./requirements/

RUN python -m pip install --upgrade pip \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r requirements/runtime.txt

# Copiar el código de la app (necesario para build de frontend)
COPY . .

# Opción C: Build de frontend en build-time (Tailwind/CSS)
# Si existe configuración de frontend del hijo, construir; si no, omitir.
RUN mkdir -p static/css \
 && if [ -f frontend/package.json ]; then \
      echo "Frontend config found; building Tailwind CSS" && \
      (cd frontend && npm ci || npm install) && \
      (cd frontend && npx tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify); \
    else \
      echo "No frontend/package.json found; skipping frontend build"; \
    fi

## Stage runtime: imagen final ligera con venv copiado
FROM python:3.11-slim-bookworm AS runtime

# Desde plantilla padre (prioridad 4): añadir PATH al venv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copiar venv desde builder
COPY --from=builder /opt/venv /opt/venv

# Copiar la app
COPY . .

# Copiar artefactos estáticos compilados desde builder
COPY --from=builder /app/static /app/static

# Crear carpeta de datos si aplica (sqlite)
RUN mkdir -p /app/src/data

# Copiar entrypoint y permisos (si fuera sobreescrito por COPY . .)
COPY scripts/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exponer puerto de la app (se mantiene 8001 del hijo)
EXPOSE 8001

# Mantener comando/entrypoint del hijo para compatibilidad
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8001"]
