# Base para ARM (Raspbian) – Python 3.11 sobre Debian Bookworm
# Usa la variante slim para tamaño moderado. En Raspberry Pi (armv7/arm64)
# Docker seleccionará automáticamente la arquitectura correcta.
FROM python:3.11-slim-bookworm AS runtime

# Evitar creación de .pyc y mejorar logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Actualizar e instalar dependencias del sistema necesarias para compilar wheels en ARM
# - build-essential, libffi-dev, libssl-dev: frecuentes para cryptography/cffi
# - cargo, rustc: por si no hay wheel precompilado de cryptography en ARM
# - git, curl: utilidades comunes
# - sqlite3, libsqlite3-dev: soporte sqlite
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

# Variables para clonar el repositorio dentro de la imagen
ARG REPO_URL=https://github.com/DarkyDieLJob/GestionFerreteria.git
ARG REPO_BRANCH=main

# Clonar código fuente dentro del contenedor (sin depender del checkout local)
RUN git clone --depth=1 --branch "${REPO_BRANCH}" "${REPO_URL}" /app

# Directorio de la app
WORKDIR /app

# Instalar dependencias base del proyecto (usar runtime.txt para producción)
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements/runtime.txt

# Crear carpetas por defecto para data/static/logs y asegurar entrypoint ejecutable
RUN mkdir -p src/data src/static logs \
    && chmod +x scripts/docker-entrypoint.sh

# Exponer puerto por defecto de Django
EXPOSE 8000

# Comando por defecto: servidor de desarrollo (puedes sobreescribir con CMD en docker run)
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]
