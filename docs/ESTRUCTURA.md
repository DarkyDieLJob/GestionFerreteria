# Estructura del Proyecto

Este proyecto utiliza Django con Arquitectura Limpia/Hexagonal. El archivo `manage.py` se encuentra dentro del directorio `src/`.

## Vista General

```
.
├── README.md
├── requirements/
├── pytest.ini
├── scripts/
├── frontend/
├── venv/                      # entorno virtual (sugerido)
└── src/
    ├── manage.py              # archivo de gestión de Django
    ├── core_config/           # configuración principal del proyecto
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── database_routers.py
    ├── core_auth/             # aplicación de autenticación (hexagonal)
    │   ├── adapters/          # capa de entrada/salida (views, forms, serializers, repositorios Django)
    │   ├── domain/            # casos de uso y contratos de dominio
    │   └── tests/             # pruebas de la app (pytest)
    ├── core_app/              # aplicación base (home, dashboard)
    ├── templates/
    └── static/                # incluye css compilado de Tailwind (static/css/tailwind.css)
```

## Capas (Hexagonal)

- Dominio (`domain/`)
  - `use_cases.py`: lógica de aplicación (Register/Login/Logout)
  - `interfaces.py`: contratos/puertos (repositorios, servicios)
- Adaptadores (`adapters/`)
  - `views.py`: adaptación HTTP (Django)
  - `forms.py`: validación de entrada
  - `serializers.py`: adaptación para APIs (DRF)
  - `repository.py`: implementación Django de interfaces de repositorio

La comunicación ideal es: View/Form -> Use Case -> Repositorio/Servicios.

## Rutas Importantes

- `src/manage.py`: comando de gestión (migrate, runserver, createsuperuser, etc.)
- `src/core_config/settings.py`: configuración del proyecto
- `src/core_config/urls.py`: enrutamiento principal

## Cómo ejecutar comandos (recordatorio)

Situarse en `src/` para utilizar `manage.py`:

```bash
# activar el entorno virtual
source ../venv/bin/activate

# migraciones
python manage.py migrate

# servidor de desarrollo
python manage.py runserver
```

## Pruebas

Los tests viven dentro de `src/` (por ejemplo, `src/core_auth/tests/`). Ejecuta pytest desde `src/` o indicando el módulo:

```bash
# desde la raíz
source venv/bin/activate
cd src
python -m pytest -q
```

### Alcance y cobertura

- Alcance de pruebas y cobertura: únicamente `core_auth` y `core_app`.
- `templates/app_templates/` es scaffolding para crear nuevas apps: está EXCLUIDO de descubrimiento de tests y de la medición de cobertura de forma permanente.
- También se excluyen `settings.py`, `asgi.py`, `wsgi.py`, `manage.py`, migraciones y archivos generados.
- La configuración (`pytest.ini` y `.coveragerc`) ya refleja estas reglas.

Para ver cobertura, revisa el resumen final que imprime `pytest-cov` (configurado en `pytest.ini`) y el reporte HTML en `htmlcov/`.
