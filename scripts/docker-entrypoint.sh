#!/usr/bin/env bash
set -euo pipefail

log() { echo -e "\n==> $1"; }

APP_DIR="/app"
cd "$APP_DIR"

# Flags de control (valores por defecto seguros)
NO_FRONTEND=${NO_FRONTEND:-false}
ENABLE_COLLECTSTATIC=${ENABLE_COLLECTSTATIC:-false}
RUN_MAKEMIGRATIONS=${RUN_MAKEMIGRATIONS:-true}

log "Flags: NO_FRONTEND=$NO_FRONTEND, ENABLE_COLLECTSTATIC=$ENABLE_COLLECTSTATIC, RUN_MAKEMIGRATIONS=$RUN_MAKEMIGRATIONS"

# 1) Preparar .env si no existe
if [[ ! -f src/.env ]]; then
  log "Preparando src/.env"
  if [[ -f src/.env.example ]]; then
    cp src/.env.example src/.env
    echo "Creado src/.env desde src/.env.example"
  else
    cat > src/.env << 'EOF'
SECRET_KEY=changeme_super_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0

NOMBRE_APLICACION=DjangoProyects
WHATSAPP_CONTACT=+00 000 000 000
PASSWORD_RESET_TICKET_TTL_HOURS=48
TEMP_PASSWORD_LENGTH=16

GITHUB_CLIENT_ID=
GITHUB_SECRET=
EOF
    echo "Creado src/.env por defecto"
  fi
fi

# 2) Frontend (Tailwind) si no se desactiva y si existe Node en runtime
if [[ "$NO_FRONTEND" != "true" ]]; then
  if command -v npm >/dev/null 2>&1; then
  log "Configurando frontend con Tailwind (npm disponible)"
  FRONTEND_DIR="frontend"
  mkdir -p "${FRONTEND_DIR}/src"

  if [[ ! -f "${FRONTEND_DIR}/package.json" ]]; then
    cat > "${FRONTEND_DIR}/package.json" << 'EOF'
{
  "name": "django-frontend",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "dev": "tailwindcss -i ./src/input.css -o ../static/css/tailwind.css -w",
    "build": "tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.10"
  }
}
EOF
  fi

  if [[ ! -f "${FRONTEND_DIR}/tailwind.config.js" ]]; then
    cat > "${FRONTEND_DIR}/tailwind.config.js" << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../src/**/*.html",
    "../src/**/templates/**/*.html",
    "../templates/**/*.html"
  ],
  theme: { extend: {} },
  plugins: [],
};
EOF
  fi

  if [[ ! -f "${FRONTEND_DIR}/postcss.config.js" ]]; then
    cat > "${FRONTEND_DIR}/postcss.config.js" << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
EOF
  fi

  if [[ ! -f "${FRONTEND_DIR}/src/input.css" ]]; then
    cat > "${FRONTEND_DIR}/src/input.css" << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF
  fi

  mkdir -p static/css
  log "Instalando dependencias npm"
  (cd "${FRONTEND_DIR}" && npm install)
  log "Construyendo CSS con Tailwind"
  (cd "${FRONTEND_DIR}" && npx tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify)
  else
    log "NO se ejecuta build de Tailwind: npm no está disponible en runtime (esperado en imágenes 'runtime')."
  fi
fi

# 3) Migraciones
if [[ "$RUN_MAKEMIGRATIONS" == "true" ]]; then
  log "Ejecutando makemigrations"
  python src/manage.py makemigrations --noinput || echo "makemigrations omitido/falló"
else
  log "RUN_MAKEMIGRATIONS=false → se omite makemigrations (migrate puede ser responsabilidad externa)."
fi

log "Aplicando migraciones"
python src/manage.py migrate --noinput

# 4) (Opcional) collectstatic (solo si el frontend no está desactivado)
if [[ "$ENABLE_COLLECTSTATIC" == "true" && "$NO_FRONTEND" != "true" ]]; then
  log "Recolectando estáticos"
  python src/manage.py collectstatic --noinput || echo "collectstatic falló/omitido"
fi

# 5) Ejecutar comando
exec "$@"
