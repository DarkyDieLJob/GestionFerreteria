# Makefile delgado: delega en project_manage.py
PY ?= python
CLI ?= project_manage.py

# Variables forward comunes
PROFILE ?=
PROFILES ?=
SERVICES ?=
FOLLOW ?=

export PROFILE PROFILES SERVICES FOLLOW

.PHONY: up down restart rebuild logs migrate status info compose clean

up:
	$(PY) $(CLI) up

down:
	$(PY) $(CLI) down

restart:
	$(PY) $(CLI) restart

rebuild:
	$(PY) $(CLI) rebuild

logs:
	$(PY) $(CLI) logs

migrate:
	$(PY) $(CLI) migrate

status:
	$(PY) $(CLI) status

info:
	$(PY) $(CLI) info

# Passthrough a docker compose: usar como `make compose ARGS="up -d --profile db"`
compose:
	$(PY) $(CLI) compose -- $(ARGS)

# Utilidad opcional
clean:
	$(PY) -c "import shutil,sys; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache','__pycache__','src/**/__pycache__','htmlcov']]" || true
	$(PY) $(CLI) down --volumes || true

# Permite que los hijos extiendan con objetivos propios
-include Makefile.local
