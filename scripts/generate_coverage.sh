#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root (this script is at scripts/generate_coverage.sh)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
SRC_DIR="${REPO_ROOT}/src"

echo "[coverage] Repo root: ${REPO_ROOT}"
cd "${REPO_ROOT}"

# Clean previous artifacts both at repo root and src for safety
rm -rf "${REPO_ROOT}/htmlcov" "${REPO_ROOT}/.coverage"* || true
rm -rf "${SRC_DIR}/htmlcov" "${SRC_DIR}/.coverage"* || true

# Coverage targets: include all first-party apps
COV_APPS=(
  core_app
  core_auth
  articulos
  proveedores
  precios
  importaciones
)

# Build repeated --cov arguments
COV_ARGS=()
for app in "${COV_APPS[@]}"; do
  COV_ARGS+=("--cov=${app}")
done

# Ensure python can import from src/
export PYTHONPATH="${SRC_DIR}:${PYTHONPATH-}"

# Run pytest from repo root, but let Django discover project via pytest.ini
# Override plugins/addopts to avoid missing custom plugin and to control reports here
echo "[coverage] Running pytest with coverage for: ${COV_APPS[*]}"
python -m pytest -q \
  -o plugins= -o addopts= \
  --maxfail=1 --disable-warnings \
  "${COV_ARGS[@]}" \
  --cov-report=term-missing:skip-covered \
  --cov-report=html

# Confirm output location for the Django view
if [[ -f "${REPO_ROOT}/htmlcov/index.html" ]]; then
  echo "[coverage] HTML report generated at ${REPO_ROOT}/htmlcov/index.html"
else
  echo "[coverage] ERROR: htmlcov/index.html was not generated at repo root" >&2
  exit 1
fi

cat <<'MSG'
[coverage] Done.
- Abra el dashboard en /dashboard/coverage/ (requiere DEBUG=True o COVERAGE_VIEW_ENABLED=True).
- Si el servidor ya está corriendo, simplemente refresque la página; si no, arránquelo con: python src/manage.py runserver
MSG
