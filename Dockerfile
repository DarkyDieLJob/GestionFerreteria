# Base para ARM (Raspbian) – Python 3.11 sobre Debian Bookworm
# Usa la variante slim para tamaño moderado. En Raspberry Pi (armv7/arm64)
# Docker seleccionará automáticamente la arquitectura correcta.
FROM python:3.11-slim-bookworm

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

# Directorio de la app
WORKDIR /app

# Primero copiar sólo requirements para aprovechar cache de capas
COPY requirements/ ./requirements/

# Instalar dependencias base del proyecto (usar runtime.txt para producción)
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements/runtime.txt

# Copiar el resto del repo
COPY . .

# Crear carpeta de datos si aplica (sqlite)
RUN mkdir -p /app/src/data

# Copiar entrypoint y dar permisos
COPY scripts/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exponer puerto por defecto de Django
EXPOSE 8000

# Comando por defecto: servidor de desarrollo (puedes sobreescribir con CMD en docker run)
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]
