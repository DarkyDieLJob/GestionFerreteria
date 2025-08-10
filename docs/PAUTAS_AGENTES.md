# Pautas para Agentes (Automatización)

Guía breve y accionable para que un agente trabaje de forma segura y reproducible en este repo.

> Importante: `manage.py` está dentro de `src/`.

## 1) Preparación y entorno

- Verificar versión de Python: `python3 --version` (>= 3.9)
- Crear y activar entorno virtual si no existe:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- Instalar dependencias (recomendado):
  ```bash
  # Nota: `lista_v3.txt` es un ejemplo heredado de otro proyecto.
  # En este repositorio, el archivo efectivo por defecto es `notebook.txt`.
  pip install -r requirements/notebook.txt
  # opcional según caso
  # pip install -r requirements/dev.txt
  # pip install -r requirements/lista_v3.txt
  ```
  Nota: alternativamente, usar los scripts de setup en `scripts/` para automatizar instalación y pruebas.
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

### 4.1 Alcance de pruebas y cobertura

- Ámbito principal: solo las apps `core_auth` y `core_app`.
- Exclusiones permanentes de pruebas y cobertura (NUNCA incluir):
  - `templates/` y, en particular, `templates/app_templates/` (scaffolding para crear nuevas apps).
  - Archivos de configuración/arranque del proyecto: `settings.py`, `asgi.py`, `wsgi.py`, `manage.py`.
  - Migraciones y archivos generados automáticamente.
- La configuración actual ya lo garantiza:
  - `pytest.ini` usa `norecursedirs = templates templates/* templates/app_templates venv .venv node_modules` para excluir el scaffolding del descubrimiento de tests.
  - `pytest.ini` limita la cobertura a `--cov=src/core_auth --cov=src/core_app`.
  - `.coveragerc` omite plantillas/scaffolding y archivos no testeables.
- Si se crea una nueva app a partir del template, moverla fuera de `templates/` antes de agregar código y tests.

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

### 7.1 Lineamientos operativos del agente

- Respetar el alcance de pruebas/cobertura: solamente `core_auth` y `core_app`.
- Nunca añadir, mover ni ejecutar tests dentro de `templates/` ni sobre `templates/app_templates/`.
- Si se requiere scaffolding para nuevas apps, utilizar `templates/app_templates/` como referencia, pero no integrarlo al árbol de `src/` hasta que sea una app real.
- Antes de proponer borrados, verificar que se trate de archivos de scaffolding no referenciados; por defecto conservar el scaffolding pero EXCLUIRLO del flujo de CI/tests.

### 7.2 Flujo de registro y recuperación (CoreAuth)

Resumen operativo del nuevo flujo seguro sin correo electrónico, con verificación por últimos 4 del DNI y entrega por WhatsApp.

- Registro de usuario (público):
  - Campos principales: usuario, email, contraseña; además:
    - Teléfono (opcional, recomendado para contacto por WhatsApp)
    - Últimos 4 del DNI (obligatorio, dato de recuperación). Se almacena hasheado.
  - Efecto: el perfil (`CoreAuthProfile`) guarda `phone_number` y `dni_last4_hash`.

- Solicitud de reseteo (pública):
  - Formulario requiere: `username`, `email`, `dni_last4` (últimos 4), `phone` (opcional).
  - No se informa si el usuario existe (mensaje neutro).
  - Se crea `PasswordResetRequest` con:
    - `short_code` único (seguimiento interno)
    - `status` inicial `pending`
    - `expires_at` según TTL de settings
  - No se envía email. El canal oficial de entrega es WhatsApp (ver `WHATSAPP_CONTACT`).

- Flujo staff (panel de staff):
  - Lista de solicitudes con estados: `pending`, `under_review`, `ready_to_deliver`, `resolved`, `expired`, `rejected`.
  - Acción "Generar temporal" (en `pending`):
    - Genera contraseña temporal (no aplicada todavía) y pasa a `ready_to_deliver`.
  - Acción "Entregar y activar" (en `ready_to_deliver`):
    - Tras verificar manualmente identidad y entregar la clave por WhatsApp, aplica la contraseña al usuario, marca `delivered_at` y `resolved`, forzando cambio al siguiente login.
  - Las expiradas (`expired`) no deben entregarse; generar una nueva si corresponde.

- Seguridad y configuración:
  - El DNI se guarda hasheado con los hashers de Django.
  - Claves temporales tienen longitud configurable y caducan por TTL.
  - Variables en `settings.py` (o `.env` según el proyecto):
    - `NOMBRE_APLICACION` (display)
    - `WHATSAPP_CONTACT` (número oficial para entrega)
    - `PASSWORD_RESET_TICKET_TTL_HOURS` (TTL por defecto: 48h)
    - `TEMP_PASSWORD_LENGTH` (por defecto: 16)
  - Hay un context processor que muestra a staff un badge con solicitudes accionables.

- Notas operativas:
  - Verificar que las plantillas públicas y de staff se correspondan con los campos/estados vigentes.
  - Registrar auditoría via campos del modelo (timestamps, `processed_by`, `delivered_at`).
  - Futuras mejoras sugeridas: rate limiting y CAPTCHA en el formulario público.

## 11) Notas sobre scaffolding de templates

- `templates/app_templates/` es una plantilla de referencia para crear nuevas apps con la arquitectura esperada (adapters/domain/ports/tests).
- Este scaffolding es parte de la documentación viva del proyecto y NUNCA debe formar parte de pruebas ni métricas de cobertura.
- Cualquier error en esos archivos no detendrá CI porque están excluidos. No deben ser corregidos salvo que se actualice el scaffolding como guía.
- Al crear una nueva app, copiar la estructura desde `templates/app_templates/` a `src/<nueva_app>/` y recién allí implementar código y tests.

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
