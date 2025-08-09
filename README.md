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

### Backend
1. Clonar el repositorio
2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # o
   .\venv\Scripts\activate  # Windows
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configurar variables de entorno en `.env`:
   ```
   SECRET_KEY=tu_clave_secreta
   DEBUG=True
   GITHUB_CLIENT_ID=tu_client_id
   GITHUB_SECRET=tu_secret
   ```
5. Migrar las bases de datos (manage.py está en `src/`):
   ```bash
   cd src
   python manage.py migrate
   ```

## Ejecución

Levantar el servidor de desarrollo (desde `src/`):

```bash
source ../venv/bin/activate  # si no está activo
python manage.py runserver
```

Accede a http://127.0.0.1:8000/

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
├── requirements.txt
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
1. **Variables de entorno**: Todas las configuraciones sensibles deben estar en `.env`
2. **Migraciones**: Cada aplicación puede tener su propia base de datos
3. **Scaffolding**: `templates/app_templates/` se usa solo como plantilla de referencia. Nunca se ejecutan tests ni se mide cobertura allí. Al crear una nueva app, copiar la estructura a `src/<nueva_app>/` y recién entonces agregar código y tests.
4. **Frontend (opcional)**: La configuración inicial debe ser recreada siguiendo las instrucciones
