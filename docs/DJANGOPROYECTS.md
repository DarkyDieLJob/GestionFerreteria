# DjangoProyects
Aplicación básica para la creación de proyectos Django con arquitectura limpia y frontend moderno.

## Tabla de Contenidos
- [Requisitos Técnicos](#requisitos-técnicos)
- [Diseño y Arquitectura](#diseño-y-arquitectura)
- [Instalación y Configuración](#instalación-y-configuración)
- [Ejecución](#ejecución)
- [Pruebas](#pruebas)
- [Estructura de Directorios](#estructura-de-directorios)

## Requisitos Técnicos

### Backend
- **Python**: 3.9+
- **Django**: 4.2.x (LTS)
- **Bases de datos**:
  - SQLite (por defecto)
  - Posibilidad de múltiples bases de datos por aplicación
- **Dependencias principales**:
  - django-allauth (autenticación social)
  - djangorestframework (APIs REST)
  - python-decouple (manejo de variables de entorno)
  - (Opcional) django-rest-framework-authtoken (autenticación por tokens)

### Frontend (opcional)
- **Node.js**: 14+
- **npm** o **yarn** para gestión de dependencias
- **Tailwind CSS** para estilos
- La configuración inicial puede mantenerse fuera del control de versiones

## Diseño y Arquitectura

### Estructura del Proyecto
- **Arquitectura limpia / hexagonal** con separación clara de responsabilidades
- **Sistema modular** con aplicaciones independientes
- **manage.py está dentro del directorio `src/`**
- (Opcional) Frontend separado en directorio `/frontend`

### Base de Datos
- **Router dinámico** en `core_config/database_routers.py`
- **Configuración automática** de bases de datos por aplicación
- **Estructura típica** para configuración de base de datos por app:
  ```python
  # En app/config.py
  DATABASE = {
      'app_name_db': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': BASE_DIR / 'data/db_app_name.sqlite3',
      }
  }
  ```

### Patrón de persistencia centralizada (persist/)

- Todos los datos no versionados (secrets, media, data, logs) se centralizan en una carpeta única por host: `persist/` fuera del repositorio.
- Bind mounts estándar desde el host al contenedor, parametrizados por `HOST_PERSIST` con default `.` para desarrollo local:
  - `${HOST_PERSIST:-.}/persist/env/.env` → `/app/src/.env` (solo lectura)
  - `${HOST_PERSIST:-.}/persist/media` → `/app/src/media`
  - `${HOST_PERSIST:-.}/persist/data` → `/app/src/data`
  - `${HOST_PERSIST:-.}/persist/logs` → `/app/logs`
- Beneficios: resiliencia ante rebuilds/restarts/compose down, backups centralizados, menor drift entre entornos.
- Tradeoffs: gestionar permisos UID/GID del usuario que ejecuta Docker/runner, .env en RO (640), menor aislamiento que named volumes pero mayor auditabilidad.
- Notas SELinux/AppArmor (si aplica): puede requerir ajustar contextos o políticas para permitir bind mounts.
  - SELinux: `chcon -Rt svirt_sandbox_file_t $HOST_PERSIST/persist` o usar `:z`/`:Z` cuando corresponda.
  - AppArmor: verificar perfiles activos y permitir montajes en la ruta destino.

### Healthchecks y orden de arranque seguro

- db (Postgres): `pg_isready` con `interval`, `timeout`, `retries` y `start_period` configurados para tolerar latencia.
- redis: `redis-cli ping` como verificación ligera del broker.
- app: `python src/manage.py check --deploy` como check ligero de Django (no depende de endpoint).
- worker (si aplica): `python src/manage.py check`.

`depends_on` con `condition: service_healthy` garantiza que `app` y `worker` esperen a `db`/`redis` listos, evitando errores por latencia o dependencias no inicializadas.

### Migraciones controladas (previas al up -d)

Ejecuta migraciones explícitamente antes de levantar servicios para evitar condiciones de carrera y arranques fallidos.

```bash
docker compose run --rm app python src/manage.py migrate
docker compose up -d [--profile db] [--profile broker] [--profile worker]
```

Beneficios: orden determinístico, menos fallos en arranque, y despliegues más estables. Tradeoff: pequeño tiempo extra en el pipeline (aceptable en producción).

### Frontend
- **Tailwind CSS** para estilos
- **Estructura típica** (opcional):
```
frontend/
├── package.json
├── tailwind.config.js
└── (otros archivos de configuración)
```

## Instalación y Configuración

### Backend (Setup rápido recomendado)
1. Clonar el repositorio
2. Ejecutar el script de setup (crea venv, instala dependencias, prepara .env, configura Tailwind y migra DB):
   - Windows (PowerShell):
     ```powershell
     powershell -ExecutionPolicy Bypass -NoLogo -NoProfile -File .\scripts\setup.ps1 -Requirements notebook -Dev
     ```
   - Linux/macOS (bash):
     ```bash
     chmod +x ./scripts/setup.sh
     ./scripts/setup.sh --requirements notebook --dev
     ```
   Notas:
   - Usa `-Requirements`/`--requirements` para elegir archivo: `dev`, `notebook`, `lista_v3` o una ruta personalizada (por defecto: `notebook`).
   - Agrega `-NoFrontend`/`--no-frontend` si quieres omitir el scaffolding de Tailwind.
   - Los scripts aseguran `djangorestframework` y `python-decouple` si faltan en el requirements elegido.

   Para más atajos, revisa la sección "Comandos rápidos" en `docs/INSTALACION.md`:
   `docs/INSTALACION.md#comandos-rápidos`.
4. Configurar variables de entorno en `src/.env` (sugerido utilizar `src/.env.example` como plantilla):
   ```
   SECRET_KEY=tu_clave_secreta
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   GITHUB_CLIENT_ID=tu_client_id
   GITHUB_SECRET=tu_secret
   NOMBRE_APLICACION=Mi Aplicacion
   WHATSAPP_CONTACT=+00 000 000 000
   PASSWORD_RESET_TICKET_TTL_HOURS=48
   TEMP_PASSWORD_LENGTH=16
   ```
5. Migrar las bases de datos (si no corriste los scripts de setup; `manage.py` está en `src/`):
   ```bash
   cd src
   python manage.py migrate
   ```

## Ejecución

Levantar el servidor de desarrollo (desde la raíz):

```bash
# Linux/macOS
./venv/bin/python ./src/manage.py runserver

# Windows (PowerShell)
./venv/Scripts/python.exe ./src/manage.py runserver
```

Accede a http://127.0.0.1:8000/

### Comandos rápidos (Windows PowerShell)

- __Setup + activar shell + correr pruebas__

  ```powershell
  powershell -ExecutionPolicy Bypass -NoLogo -NoProfile -File .\scripts\setup.ps1 -Requirements notebook -Dev -ActivateShell -Test
  ```

- __Setup + pruebas y lanzar server si todo pasa__

  ```powershell
  powershell -ExecutionPolicy Bypass -NoLogo -NoProfile -File .\scripts\setup.ps1 -Requirements notebook -Dev -ActivateShell -Test -RunServer
  ```

- __Activar entorno y correr pruebas manualmente__

  ```powershell
  .\venv\Scripts\Activate
  python -m pytest -q .\src
  ```

- __Lanzar servidor manualmente__

  ```powershell
  .\venv\Scripts\python .\src\manage.py runserver 0.0.0.0:8000
  ```

### Crear superusuario (admin)

Desde la raíz del proyecto, con el entorno activado:

- Windows (PowerShell):

  ```powershell
  .\venv\Scripts\Activate
  python .\src\manage.py createsuperuser
  ```

- Linux/macOS (bash):

  ```bash
  source ./venv/bin/activate
  python ./src/manage.py createsuperuser
  ```

Sigue las indicaciones (usuario, email opcional y contraseña). Luego inicia sesión en `/admin/`.

## Pruebas

Ejecutar la suite de tests con pytest (los tests están bajo `src/`):

```bash
source venv/bin/activate      # desde la raíz del proyecto
cd src
python -m pytest -q
```

### Alcance de pruebas y cobertura

- La cobertura y las pruebas están enfocadas únicamente en las apps `core_auth` y `core_app`.
- `templates/app_templates/` es scaffolding (plantilla para crear nuevas apps) y está EXCLUIDO de descubrimiento de tests y de cobertura de forma permanente.
- También se excluyen archivos no testeables como `settings.py`, `asgi.py`, `wsgi.py`, `manage.py`, migraciones y artefactos generados.
- La configuración (`pytest.ini` y `.coveragerc`) ya refleja estas reglas.

#### Vista de cobertura (solo staff)

- Existe una vista protegida para ver el reporte HTML de cobertura dentro de la app: `/coverage/`.
- Protección: requiere usuario staff (`@staff_member_required`).
- Disponibilidad: solo si `DEBUG=True` o si `COVERAGE_VIEW_ENABLED=True` en los settings del entorno.
- Fuente: sirve el archivo `htmlcov/index.html` generado por `pytest --cov`.
- En CI (GitHub Actions) el reporte se publica como artifact del job (no en la app). Solo es accesible para usuarios con acceso al repo.

### Frontend
1. Navegar al directorio del frontend:
   ```bash
   cd frontend
   ```
2. Instalar dependencias:
   ```bash
   npm install
   # o
   yarn
   ```
3. Configurar Tailwind CSS (si es necesario)
4. Iniciar el servidor de desarrollo:
   ```bash
   npm run dev
   # o
   yarn dev
   ```

## Estructura de Directorios
```
.
├── README.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirements/              # archivos de dependencias
│   ├── dev.txt
│   ├── notebook.txt
│   ├── lista_v3.txt
│   └── runtime.txt            # dependencias mínimas de ejecución (Docker)
├── scripts/                   # scripts de automatización
│   ├── setup.ps1              # Windows (PowerShell)
│   ├── setup.sh               # Linux/macOS (bash)
│   └── docker-entrypoint.sh   # entrypoint del contenedor
├── frontend/                  # Tailwind (generado por scripts)
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/input.css
├── static/
│   └── css/tailwind.css       # salida compilada de Tailwind
├── pytest.ini
├── venv/                      # entorno virtual (sugerido)
└── src/
    ├── manage.py              # archivo de gestión de Django
    ├── core_config/           # configuración principal del proyecto
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── database_routers.py
    ├── core_auth/             # aplicación de autenticación (arquitectura hexagonal)
    │   ├── adapters/
    │   ├── domain/
    │   └── tests/
    ├── core_app/              # aplicación base (home, dashboard)
    ├── templates/             # incluye `templates/app_templates/` como scaffolding (EXCLUIDO de tests/cobertura)
    └── static/
```

## Consideraciones Importantes
1. **Variables de entorno**: Todas las configuraciones sensibles deben estar en `src/.env` (usa `src/.env.example` como plantilla)
2. **Migraciones**: Cada aplicación puede tener su propia base de datos
3. **Scaffolding**: `templates/app_templates/` se usa solo como plantilla de referencia. Nunca se ejecutan tests ni se mide cobertura allí. Al crear una nueva app, copiar la estructura a `src/<nueva_app>/` y recién entonces agregar código y tests.
4. **Frontend**: Los scripts generan `frontend/` y compilan Tailwind a `static/css/tailwind.css`. Incluye el CSS en tus plantillas con `{% static 'css/tailwind.css' %}`.

## Perfiles de build y frontend condicional

- **Objetivo**: permitir imágenes de producción ligeras sin Node/npm cuando el frontend no es necesario, y habilitar un target alternativo con assets precompilados cuando sí se requiere.

- **Targets del Dockerfile**:
  - `runtime`: imagen final sin Node/npm (recomendada para producción sin frontend).
  - `runtime-frontend`: imagen final que copia los estáticos construidos por un stage Node (sin incluir Node en runtime).

- **Build recomendado (buildx)**:
  - Sin frontend (amd64):
    ```bash
    docker buildx build --target runtime --platform linux/amd64 -t app:latest .
    ```
  - Con frontend (amd64):
    ```bash
    docker buildx build --target runtime-frontend --platform linux/amd64 -t app:with-frontend .
    ```
  - ARM (RPi): arm64
    ```bash
    docker buildx build --target runtime --platform linux/arm64 -t app:arm64 .
    ```
  - ARM (RPi): armv7
    ```bash
    docker buildx build --target runtime --platform linux/arm/v7 -t app:armv7 .
    ```

- **Flags de runtime (entrypoint)**:
  - `NO_FRONTEND=true`: desactiva pasos de Node/Tailwind en runtime.
  - `ENABLE_COLLECTSTATIC=true`: ejecuta `collectstatic` en arranque (opcional).
  - `RUN_MAKEMIGRATIONS=false`: desactiva `makemigrations` en arranque (por defecto true en la plantilla).

- **Notas**:
  - Preferir `--target` por sobre `--build-arg ENABLE_FRONTEND=0` para evitar construir stages innecesarios.
  - El stage `runtime-frontend` copia únicamente los artefactos requeridos (por ejemplo, `static/css/tailwind.css`).
  - Integración con Compose: activar el perfil `frontend` solo cuando se utilice `runtime-frontend` y/o se necesite servir assets adicionales.

### Ignorados recomendados y por qué

- **Runtime/artefactos** (frontend/, node_modules/, src/static/, src/staticfiles/, src/media/, logs/): generados en build/ejecución, reproducibles; no deben entrar al historial.
- **Persistencia y secretos** (/persist/**, src/.env, .env*): la persistencia vive fuera del repo; ignorar secretos evita fugas accidentales.
- **Caches/cobertura** (__pycache__/, .pytest_cache/, htmlcov/, .coverage*): ruido y tamaño innecesario.
- **Migraciones (plantilla)**: ignoramos `src/**/migrations/*.py` salvo `__init__.py` para evitar acoplar el template a un estado de DB concreto. Los hijos pueden versionarlas con un override local si lo requieren.
- **IDEs/tooling** (.idea/, .vscode/, .ruff_cache/, .ipynb_checkpoints/, .mypy_cache/, .pytype/): específicos del entorno del desarrollador.

Overrides en hijos (si necesitan versionar algo ignorado):

```gitignore
!src/**/migrations/*.py
# o granular, por app
!src/app_x/migrations/*.py
```

Sugerencia: si empleas pre-commit, agrega un hook que alerte sobre intentos de commitear `.env` o `persist/`.

## Flujo de ramas y commits (resumen)

Sigue `docs/GIT_AGENTES.md`:

- Nunca trabajes directo en `main` o `pre-release`.
- Si estás en `develop`: crea una rama `feature/{area}/{descripcion}` para empezar cambios.
- Si estás en `pre-release` o `main`:
  - Cambia a la rama `feature/*` pertinente, o
  - Cambia a `develop` y crea la `feature/*` correspondiente.

Convencional Commits (resumen):

- Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
- Ejemplos para esta dockerización:
  - `feat(docker): agregar Dockerfile y entrypoint con build de Tailwind`
  - `chore(docker): añadir .dockerignore`
  - `feat(deps): crear requirements/runtime.txt para producción`
  - `docs(docker): instrucciones de build y uso (compose con restart always)`
