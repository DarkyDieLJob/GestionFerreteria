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
# Genera configuración mínima si el repo no la trae (mantiene compatibilidad del hijo)
RUN mkdir -p frontend/src static/css \
 && if [ ! -f frontend/package.json ]; then cat > frontend/package.json << 'EOF'\
{\
  "name": "django-frontend",\
  "private": true,\
  "version": "0.1.0",\
  "scripts": {\
    "dev": "tailwindcss -i ./src/input.css -o ../static/css/tailwind.css -w",\
    "build": "tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify"\
  },\
  "devDependencies": {\
    "autoprefixer": "^10.4.19",\
    "postcss": "^8.4.38",\
    "tailwindcss": "^3.4.10"\
  }\
}\
EOF\
; fi \
 && if [ ! -f frontend/tailwind.config.js ]; then cat > frontend/tailwind.config.js << 'EOF'\
/** @type {import('tailwindcss').Config} */\
module.exports = {\
  content: [\
    "../src/**/*.html",\
    "../src/**/templates/**/*.html",\
    "../templates/**/*.html"\
  ],\
  theme: { extend: {} },\
  plugins: [],\
};\
EOF\
; fi \
 && if [ ! -f frontend/postcss.config.js ]; then cat > frontend/postcss.config.js << 'EOF'\
module.exports = {\
  plugins: {\
    tailwindcss: {},\
    autoprefixer: {},\
  },\
};\
EOF\
; fi \
 && if [ ! -f frontend/src/input.css ]; then cat > frontend/src/input.css << 'EOF'\
@tailwind base;\
@tailwind components;\
@tailwind utilities;\
EOF\
; fi \
 && (cd frontend && npm ci || npm install) \
 && (cd frontend && npx tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify)

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
