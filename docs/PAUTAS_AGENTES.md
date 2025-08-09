# Pautas para Agentes (Automatización)

Guía breve y accionable para que un agente trabaje de forma segura y reproducible en este repo.

> Importante: `manage.py` está dentro de `src/`.

## 1) Preparación y entorno

- Verificar versión de Python: `python3 --version` (>= 3.10)
- Crear y activar entorno virtual si no existe:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- Instalar dependencias:
  ```bash
  pip install -r requirements.txt
  ```
- Confirmar que el archivo de entorno existe en `src/.env`. Si no, crearlo (ver docs/INSTALACION.md).

## 2) Ubicación de comandos

- Siempre ejecutar comandos de Django desde `src/` (donde está `manage.py`). Ejemplos:
  ```bash
  cd src
  python manage.py migrate
  python manage.py runserver
  ```
- Ejecutar pruebas también desde `src/`:
  ```bash
  python -m pytest -q
  ```

## 3) Flujo de trabajo estándar

1. Activar venv
2. Instalar/actualizar dependencias si es necesario
3. Asegurar `src/.env` válido
4. `cd src`
5. Migraciones: `python manage.py migrate`
6. Correr pruebas: `python -m pytest -q`
7. Levantar servidor si aplica: `python manage.py runserver`

## 4) Pruebas y cobertura

- Ejecutar suite completa: `python -m pytest -q`
- Si hay fallos, leer los mensajes y corregir antes de continuar
- Los tests residen bajo `src/` (p. ej. `src/core_auth/tests/`)

## 5) Convenciones de código (resumen)

- Arquitectura hexagonal: preferir lógica en `domain/use_cases.py`, vistas/adaptadores en `adapters/`
- No mutar internals de excepciones de Django (p. ej. `ValidationError`); re-lanzar con datos limpios
- Mensajes al usuario mediante framework de mensajes de Django
- Redirecciones: mantener consistencia con las pruebas (ver `core_auth/adapters/views.py`)

## 6) Operaciones comunes

- Crear superusuario (opcional):
  ```bash
  cd src
  python manage.py createsuperuser
  ```
- Recopilar estáticos (si corresponde):
  ```bash
  python manage.py collectstatic --noinput
  ```

## 7) Seguridad y buenas prácticas para agentes

- No ejecutar comandos destructivos sin respaldo (rm -rf, etc.)
- No exponer claves; mantener `.env` fuera del control de versiones
- Validar que `venv` esté activo antes de ejecutar `manage.py`/pytest
- Evitar modificar múltiples archivos grandes de una sola vez; preferir cambios pequeños con pruebas
- Documentar cambios relevantes en Markdown (README.md, docs/)

## 8) Atajos útiles

- Correr un subconjunto de tests:
  ```bash
  python -m pytest -q -k "login or logout"
  ```
- Ver fallos recientes con detalles:
  ```bash
  python -m pytest -rfExX --maxfail=1
  ```

## 9) Problemas frecuentes

- Redirecciones inesperadas con `?next=`: revisar `success_url` y vistas (Logout/Login)
- Errores de mensajes no capturados en tests: asegurar uso de `messages.error()` o `request._messages.error()` cuando se mockea
- Tests no descubiertos: confirmar ejecución desde `src/` y configuración de `pytest.ini`

## 10) Referencias

- docs/INSTALACION.md: instalación paso a paso
- docs/ESTRUCTURA.md: estructura/arquitectura del proyecto
- README.md: guía general
