# Estructura del Proyecto Base

Este documento describe la estructura de un proyecto base en Django, diseñado como punto de partida para nuevos proyectos. Utiliza una **arquitectura hexagonal** para garantizar modularidad, testabilidad y separación de preocupaciones. Incluye soporte para inicio de sesión con y sin redes sociales, Django REST Framework (DRF) con autenticación por tokens, y endpoints REST opcionales. Cada aplicación puede definir su propia base de datos en `config.py`, con una base de datos por defecto (`default`) para aplicaciones sin requisitos específicos.

## Carpetas Principales

- **`src/`**: Contiene el código fuente del proyecto.
  - **`core_config/`**: Configuración global del proyecto.
    - `settings.py`: Configuración de Django (bases de datos, autenticación, DRF, etc.).
    - `urls.py`: URLs globales del proyecto.
    - `wsgi.py` y `asgi.py`: Configuración para despliegue.
    - `database_routers.py`: Router para manejar múltiples bases de datos.
  - **`data/`**: Almacena archivos de bases de datos (ej. `db_default.sqlite3`, `db_core_app.sqlite3`).
  - **`core_app/`**: Aplicación para gestionar artículos (conectada a `core_app_db`).
    - `config.py`: Configuración de la base de datos `core_app_db`.
    - `domain/`:
      - `use_cases.py`: Casos de uso para artículos (ej. listar, buscar).
    - `ports/`:
      - `interfaces.py`: Interfaces para interactuar con adaptadores (ej. `ArticleRepository`).
    - `adapters/`:
      - `models.py`: Modelos para artículos.
      - `views.py`: Vistas para la UI de artículos.
      - `serializers.py`: Serializadores para endpoints REST.
      - `urls.py`: URLs específicas de la aplicación.
      - `repository.py`: Adaptador para conectar con `core_app_db`.
    - `templates/`:
      - `core_app/`:
        - `base.html`: Plantilla base para la UI.
      - `auth/`:
        - `login.html`: Formulario de inicio de sesión.
        - `register.html`: Formulario de registro.
    - `tests/`:
      - `test_use_cases.py`: Pruebas para casos de uso.
      - `test_adapters.py`: Pruebas para adaptadores.
    - `admin.py`: Configuración del panel de administración.
    - `apps.py`: Configuración de la aplicación.
    - `migrations/`:
      - `__init__.py`: Directorio para migraciones.

- **`docs/`**: Documentación del proyecto.
  - `adr/`:
    - `0001-adopcion-arquitectura-hexagonal.md`: Decisión sobre la arquitectura.
  - `api/`: Documentación de la API REST (pendiente).
  - `user/`: Guías para usuarios finales (pendiente).

- **`requirements/`**:
  - `dev.txt`: Dependencias para desarrollo (pytest, black, flake8).
  - `lista_v3.txt`: Dependencias base (Django, DRF, django-allauth, etc.).
  - `notebook.txt`: Dependencias adicionales (si aplica).

- **`templates/`**:
  - `app_template/`:
    - Plantilla para nuevas aplicaciones con estructura hexagonal (usada con `startapp --template`).

## Archivos en la Raíz

- **`manage.py`**: Script principal de Django para ejecutar comandos administrativos.
- **`project_structure.md`**: Este archivo, que describe la estructura.
- **`objectives.md`**: Pasos para implementar el proyecto.
- **`README.md`**: Instrucciones para configurar y ejecutar el proyecto.
- **`LICENSE`**: Licencia del proyecto (ej. MIT).
- **`.gitignore`**: Ignora archivos generados y sensibles (ej. `.env`, `__pycache__`, `data/*.sqlite3`).

## Arquitectura Hexagonal

El proyecto sigue una **arquitectura hexagonal** para garantizar:
- **Dominio**: Casos de uso en `domain/use_cases.py` encapsulan la lógica de negocio.
- **Puertos**: Interfaces en `ports/interfaces.py` definen contratos entre el dominio y los adaptadores.
- **Adaptadores**: Implementaciones específicas (modelos, vistas, serializadores, repositorios) en `adapters/`.
- **Múltiples bases de datos**:
  - `default`: Para aplicaciones sin base de datos específica (ej. `core_auth`).
  - `core_app_db`: Para datos de artículos, conectada a `core_app`.
  - Nuevas aplicaciones pueden definir su base de datos en `config.py`.

## Detalles de Implementación

- **Autenticación**: Pendiente de implementación en `core_auth`.
- **API REST**: Pendiente de implementación en `api`.
- **Pruebas**: Estructuradas por casos de uso y adaptadores, ejecutadas con `pytest`.
- **Bases de datos**:
  - Configuradas dinámicamente desde `config.py` de cada aplicación.
  - Almacenadas en `src/data/` (ej. `db_default.sqlite3`, `db_core_app.sqlite3`).
  - Router en `core_config/database_routers.py` dirige operaciones.

## Notas Adicionales

- Nuevas aplicaciones se crean en `src/` usando `python manage.py startapp <nombre> --template=../templates/app_template`.
- Cada aplicación define su base de datos en `config.py` y se registra automáticamente en `settings.py`.
- Los endpoints REST son opcionales y se implementarán en `api/` si son necesarios.
- Mantén la documentación actualizada en `docs/` y usa ADRs para decisiones clave.