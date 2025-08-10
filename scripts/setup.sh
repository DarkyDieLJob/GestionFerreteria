#!/usr/bin/env bash
#
# Setup del proyecto en Linux/macOS (bash)
# - Crea venv, instala dependencias, genera .env si falta, migra DB
# - Flags opcionales: --dev para deps de desarrollo, --test para correr tests, --skip-migrate para omitir migraciones
# - --requirements <nombre|ruta> para elegir qué archivo de requirements instalar (dev|notebook|lista_v3|ruta)
# - --no-frontend para saltar scaffolding de frontend (Tailwind)
#
set -euo pipefail

DEV=false
TEST=false
SKIP_MIGRATE=false
REQUIREMENTS="notebook"
NO_FRONTEND=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dev)
      DEV=true
      shift
      ;;
    --test)
      TEST=true
      shift
      ;;
    --skip-migrate)
      SKIP_MIGRATE=true
      shift
      ;;
    --requirements)
      REQUIREMENTS=${2:-}
      if [[ -z "$REQUIREMENTS" ]]; then echo "--requirements requiere un valor" >&2; exit 1; fi
      shift 2
      ;;
    --no-frontend)
      NO_FRONTEND=true
      shift
      ;;
    *)
      echo "Argumento no reconocido: $1" >&2
      exit 1
      ;;
  esac
done

stage() { echo -e "\n==> $1"; }

# 1) Resolver python3
stage "Verificando Python3"
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 no encontrado. Instala Python 3.10+ y reintenta." >&2
  exit 1
fi

# 2) Crear venv
stage "Creando entorno virtual (venv)"
if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

# 3) Actualizar pip
stage "Actualizando pip"
./venv/bin/python -m pip install --upgrade pip

# 4) Instalar dependencias base (según selección)
stage "Seleccionando requirements: $REQUIREMENTS"
REQ_DIR="requirements"
case "$REQUIREMENTS" in
  [Dd][Ee][Vv])        REQ_BASE="$REQ_DIR/dev.txt" ;;
  [Nn][Oo][Tt][Ee][Bb][Oo][Oo][Kk]) REQ_BASE="$REQ_DIR/notebook.txt" ;;
  [Ll][Ii][Ss][Tt][Aa]_[Vv]3|[Ll][Ii][Ss][Tt][Aa][Vv]3) REQ_BASE="$REQ_DIR/lista_v3.txt" ;;
  *)
    if [[ -f "$REQUIREMENTS" ]]; then REQ_BASE="$REQUIREMENTS"; else
      echo "No se reconoce requirements '$REQUIREMENTS'. Use dev|notebook|lista_v3 o una ruta válida." >&2; exit 1;
    fi
    ;;
esac
stage "Instalando dependencias base ($REQ_BASE)"
./venv/bin/python -m pip install -r "$REQ_BASE"

# 5) Paquetes requeridos no listados explícitamente
stage "Asegurando paquetes requeridos (djangorestframework, python-decouple)"
./venv/bin/python -m pip install djangorestframework python-decouple

# 6) Dependencias de desarrollo (opcional)
if [[ "$DEV" == "true" ]]; then
  stage "Instalando dependencias de desarrollo (requirements/dev.txt)"
  REQ_DEV="requirements/dev.txt"
  if [[ -f "$REQ_DEV" ]]; then
    ./venv/bin/python -m pip install -r "$REQ_DEV"
  else
    echo "No se encontró requirements/dev.txt, se omite."
  fi
fi

# 7) .env
stage "Preparando archivo de entorno src/.env"
if [[ ! -f src/.env ]]; then
  if [[ -f src/.env.example ]]; then
    cp src/.env.example src/.env
    echo "Creado src/.env desde src/.env.example"
  else
    cat > src/.env << 'EOF'
SECRET_KEY=changeme_super_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

NOMBRE_APLICACION=DjangoProyects
WHATSAPP_CONTACT=+00 000 000 000
PASSWORD_RESET_TICKET_TTL_HOURS=48
TEMP_PASSWORD_LENGTH=16

GITHUB_CLIENT_ID=
GITHUB_SECRET=
EOF
    echo "Creado src/.env por defecto"
  fi
else
  echo "src/.env ya existe, no se modifica."
fi

# 7.1) Frontend (Tailwind) por defecto a menos que se desactive
if [[ "$NO_FRONTEND" != "true" ]]; then
  stage "Configurando frontend con Tailwind"
  FRONTEND_DIR="frontend"
  mkdir -p "$FRONTEND_DIR/src"

  if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
    cat > "$FRONTEND_DIR/package.json" << 'EOF'
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

  if [[ ! -f "$FRONTEND_DIR/tailwind.config.js" ]]; then
    cat > "$FRONTEND_DIR/tailwind.config.js" << 'EOF'
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

  if [[ ! -f "$FRONTEND_DIR/postcss.config.js" ]]; then
    cat > "$FRONTEND_DIR/postcss.config.js" << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
EOF
  fi

  if [[ ! -f "$FRONTEND_DIR/src/input.css" ]]; then
    cat > "$FRONTEND_DIR/src/input.css" << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF
  fi

  mkdir -p static/css
  if command -v npm >/dev/null 2>&1; then
    stage "Instalando dependencias npm"
    (cd "$FRONTEND_DIR" && npm install)
    stage "Construyendo CSS con Tailwind"
    (cd "$FRONTEND_DIR" && npx tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify)
  else
    echo "npm no encontrado. Ejecuta 'npm install' y 'npm run build' dentro de frontend/ cuando tengas Node.js."
  fi
fi

# 8) Migraciones
if [[ "$SKIP_MIGRATE" != "true" ]]; then
  stage "Ejecutando migraciones"
  ./venv/bin/python ./src/manage.py migrate
fi

# 9) Tests (opcional)
if [[ "$TEST" == "true" ]]; then
  stage "Ejecutando tests (pytest)"
  if ./venv/bin/python -m pytest -q ./src; then
    echo "Tests OK"
  else
    echo "Pytest no disponible o falló. Instala --dev para incluirlo." >&2
  fi
fi

echo -e "\nSetup completado. Para ejecutar el servidor:"
echo "./venv/bin/python ./src/manage.py runserver"
