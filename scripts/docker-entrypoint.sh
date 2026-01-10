#!/usr/bin/env bash
set -euo pipefail

log() { echo -e "\n==> $1"; }

APP_DIR="/app"
cd "$APP_DIR"

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

PROJECT_MODE=local
TABLET_MODE=false

GITHUB_CLIENT_ID=
GITHUB_SECRET=
EOF
    echo "Creado src/.env por defecto"
  fi
fi

# 2) Frontend (Tailwind) si no se desactiva
if [[ "${NO_FRONTEND:-false}" != "true" ]]; then
  log "Configurando frontend con Tailwind"
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
fi

# 3) Migraciones
log "Generando migraciones"
python src/manage.py makemigrations
log "Aplicando migraciones"
python src/manage.py migrate --noinput

# 4) (Opcional) collectstatic
if [[ "${ENABLE_COLLECTSTATIC:-false}" == "true" ]]; then
  log "Recolectando estáticos"
  python src/manage.py collectstatic --noinput || echo "collectstatic falló/omitido"
fi

# 5) Ejecutar comando
exec "$@"
