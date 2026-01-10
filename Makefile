# Atajos de gestión (requiere docker compose v2)

.PHONY: rebuild restart up down logs trigger status

rebuild:
	python project_manage.py rebuild

restart:
	python project_manage.py restart

up:
	python project_manage.py up

down:
	python project_manage.py down

# Uso: make logs SERVICE=worker  (o app)
logs:
	python project_manage.py logs $(SERVICE)

trigger:
	python project_manage.py trigger

# Uso: make status SECTION=scheduled
status:
	python project_manage.py status $(SECTION)
