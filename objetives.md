# Objetivos para Implementar el Proyecto Base

> Nota: El flujo recomendado hoy es clonar el repo y usar los scripts de setup multiplataforma. La guía de creación "desde cero" que sigue se mantiene como referencia histórica.

## Flujo Rápido (clonación + scripts)

- Clona el repo y entra a la carpeta raíz del proyecto.
- Windows (PowerShell):
  ```powershell
  scripts/setup.ps1 -Requirements lista_v3 -ActivateShell -Test -RunServer
  ```
- Linux/macOS (bash):
  ```bash
  bash scripts/setup.sh --requirements lista_v3 --test
  ```
- Variables de entorno: copia `src/.env.example` a `src/.env` y ajusta valores.
- Crear superusuario (desde `src/` con venv activo):
  ```powershell
  python manage.py createsuperuser
  ```
- Consulta `README.md` para más detalles de opciones (`dev`, `notebook`, integración de frontend con Tailwind, etc.).

Este documento detalla los pasos necesarios para completar la implementación del proyecto base en Django con **arquitectura hexagonal**, diseñado para ser clonado y extendido en nuevos proyectos. Incluye autenticación local y social, endpoints REST opcionales con autenticación por tokens, soporte para que cada aplicación defina su propia base de datos, y una plantilla personalizada para `startapp`.

## Pasos para Completar el Proyecto Base

1. **Configurar el Proyecto Django**
   - Ejecutar:
     ```bash
     mkdir DjangoProyects
     cd DjangoProyects
     python -m venv venv
     source venv/bin/activate  # En Windows: venv\Scripts\activate
     pip install django djangorestframework django-allauth pytest pytest-django pytest-cov
     pip freeze > requirements/lista_v3.txt
     echo "pytest\npytest-django\npytest-cov\nblack\nflake8" > requirements/dev.txt
     django-admin startproject core_config src
     mv src/manage.py .
     mkdir src/data
     cd src
     python ../manage.py startapp core_app --template=../templates/app_template
     python ../manage.py startapp core_auth --template=../templates/app_template
     python ../manage.py startapp api --template=../templates/app_template
     python ../manage.py startapp core_utils --template=../templates/app_template
     python ../manage.py startapp cart --template=../templates/app_template
     mkdir src/core_app/templates/auth
     touch src/core_app/templates/auth/login.html src/core_app/templates/auth/register.html
     ```
   - Configurar `src/core_config/settings.py` con:
     - Base de datos por defecto:
       ```python
       DATABASES = {
           'default': {
               'ENGINE': 'django.db.backends.sqlite3',
               'NAME': BASE_DIR / 'data/db_default.sqlite3',
           }
       }
       ```
     - Carga dinámica de bases de datos desde `config.py`:
       ```python
       import importlib
       for app in INSTALLED_APPS:
           if app.startswith('core_') or app in ['cart', 'api']:
               try:
                   module = importlib.import_module(f'{app.split(".")[0]}.config')
                   DATABASES.update(getattr(module, 'DATABASE', {}))
               except (ImportError, AttributeError):
                   pass
       ```
     - `INSTALLED_APPS`, `AUTHENTICATION_BACKENDS`, `REST_FRAMEWORK`, y `DATABASE_ROUTERS`.
   - Crear `src/core_config/database_routers.py` para dirigir operaciones.
   - Crear estructura de carpetas (`docs/`, `requirements/`, `templates/app_template/`).
   - **Tiempo estimado**: 1-2 días.

2. **Crear Plantilla para Nuevas Aplicaciones**
   - Crear `templates/app_template/` con la estructura hexagonal:
     - `config.py`: Define la base de datos (`{{ app_name }}_db`).
     - `domain/use_cases.py`, `ports/interfaces.py`, `adapters/` (con `urls.py`), `templates/{{ app_name }}/`, `tests/`.
   - Usar con `python manage.py startapp <nombre> --template=../templates/app_template`.
   - **Tiempo estimado**: 1 día.

3. **Implementar Autenticación**
   - Configurar `django-allauth` en `core_auth`:
     - Configurar `SOCIALACCOUNT_PROVIDERS` en `settings.py`.
     - Crear vistas y plantillas en `core_auth/adapters/views.py` y `core_auth/templates/auth/`.
     - Implementar casos de uso en `core_auth/domain/use_cases.py`.
     - Definir interfaces en `core_auth/ports/interfaces.py`.
   - Implementar autenticación por tokens para DRF:
     - Configurar `rest_framework.authtoken` en `INSTALLED_APPS`.
     - Crear endpoints en `api/adapters/views.py`.
   - **Tiempo estimado**: 2-3 días.

4. **Configurar la Arquitectura Hexagonal**
   - En `core_app` (para artículos, conectado a `core_app_db`):
     - Usar `config.py` para definir `core_app_db`.
     - Implementar casos de uso, interfaces, y adaptadores.
   - En `cart` (para carrito, conectado a `cart_db`):
     - Usar `config.py` para definir `cart_db`.
     - Implementar casos de uso, interfaces, y adaptadores.
   - En `core_utils`:
     - Crear `helpers.py` con funciones auxiliares.
   - En `api`:
     - Crear endpoints REST de ejemplo, protegidos con `TokenAuthentication`.
   - **Tiempo estimado**: 4-5 días.

5. **Escribir Pruebas**
   - En `core_app/tests/`, `cart/tests/`, `core_auth/tests/`:
     - `test_use_cases.py`: Pruebas unitarias para casos de uso.
     - `test_adapters.py`: Pruebas para adaptadores.
   - En `api/tests/`:
     - `test_api.py`: Pruebas para endpoints REST.
   - Usar `pytest` y apuntar a una cobertura del 80% (usar `pytest-cov`).
   - **Tiempo estimado**: 2-3 días.

6. **Configurar CI/CD con GitHub Actions**
   - Crear `.github/workflows/ci.yml` para:
     - Ejecutar pruebas con `pytest`.
     - Instalar dependencias desde `requirements/lista_v3.txt`.
   - Ejemplo:
     ```yaml
     name: CI
     on:
       push:
         branches: [ main ]
       pull_request:
         branches: [ main ]
     jobs:
       test:
         runs-on: ubuntu-latest
         steps:
         - uses: actions/checkout@v2
         - name: Set up Python
           uses: actions/setup-python@v2
           with:
             python-version: '3.8'
         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -r requirements/lista_v3.txt
         - name: Run tests
           run: python manage.py test
     ```
   - **Tiempo estimado**: 1 día.

7. **Documentar el Proyecto**
   - Crear `README.md` con instrucciones para:
     - Instalar dependencias.
     - Configurar variables de entorno (`.env`).
     - Ejecutar migraciones para todas las bases de datos.
     - Crear nuevas aplicaciones con `startapp --template`.
   - Crear documentación en `docs/`:
     - Guía de instalación en `docs/user/`.
     - Documentación de la API en `docs/api/`.
   - **Tiempo estimado**: 1 día.

8. **Preparar para Clonación**
   - Crear `.env.example` con variables de entorno (ej. `SECRET_KEY`, `SOCIAL_AUTH_GOOGLE_CLIENT_ID`).
   - Incluir `scripts/create_app.sh` para automatizar la creación de aplicaciones.
   - Verificar que `.gitignore` incluya `data/*.sqlite3`, `.env`, `__pycache__`.
   - Subir el proyecto a un repositorio Git con una licencia (ej. MIT).
   - **Tiempo estimado**: 1 día.

## Notas para Clonación
- Clonar el repositorio.
- Copiar `.env.example` a `.env` y configurar variables.
- Instalar dependencias (`pip install -r requirements/lista_v3.txt`).
- Ejecutar migraciones:
  ```bash
  python manage.py migrate --database=default
  python manage.py migrate --database=core_app_db
  ```
- Crear nuevas aplicaciones:
  ```bash
  cd src
  python ../manage.py startapp <nombre> --template=../templates/app_template
  ```
- Actualizar `INSTALLED_APPS` y `database_routers.py` para nuevas aplicaciones.

## Tiempo Total Estimado
- Aproximadamente **13-17 días** debido a la complejidad de la arquitectura hexagonal, múltiples bases de datos, y la plantilla personalizada.

## Prioridades
- Configurar la plantilla `startapp` para automatizar la creación de aplicaciones.
- Implementar `core_app` y `core_auth` con sus bases de datos.
- Asegurar que el router y la carga dinámica de bases de datos funcionen correctamente.
- Documentar cada paso para facilitar la extensión del proyecto.