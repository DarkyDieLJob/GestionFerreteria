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
- **Python**: 3.10+
- **Django**: 5.2+
- **Bases de datos**:
  - SQLite (por defecto)
  - Posibilidad de múltiples bases de datos por aplicación
- **Dependencias principales**:
  - django-allauth (autenticación social)
  - djangorestframework (APIs REST)
  - python-decouple (manejo de variables de entorno)
  - django-rest-framework-authtoken (autenticación por tokens)

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
4. Configurar variables de entorno en `.env`:
   ```
   SECRET_KEY=tu_clave_secreta
   DEBUG=True
   GITHUB_CLIENT_ID=tu_client_id
   GITHUB_SECRET=tu_secret
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
├── requirements/              # archivos de dependencias
│   ├── dev.txt
│   ├── notebook.txt
│   └── lista_v3.txt
├── scripts/                   # scripts de automatización
│   ├── setup.ps1              # Windows (PowerShell)
│   └── setup.sh               # Linux/macOS (bash)
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
