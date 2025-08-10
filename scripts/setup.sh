#!/usr/bin/env bash
#
# Setup del proyecto en Linux/macOS (bash)
# - Crea venv, instala dependencias, genera .env si falta, migra DB
# - Flags opcionales: --dev para deps de desarrollo, --test para correr tests, --skip-migrate para omitir migraciones
#
set -euo pipefail

DEV=false
TEST=false
SKIP_MIGRATE=false

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

# 4) Instalar dependencias base
stage "Instalando dependencias base (requirements/lista_v3.txt)"
REQ_BASE="requirements/lista_v3.txt"
if [[ ! -f "$REQ_BASE" ]]; then
  echo "No existe $REQ_BASE" >&2
  exit 1
fi
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
