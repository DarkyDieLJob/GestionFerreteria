# DjangoProyects
Aplicación básica para la creación de proyectos Django con arquitectura limpia y frontend moderno.

## Tabla de Contenidos
- [Requisitos Técnicos](#requisitos-técnicos)
- [Diseño y Arquitectura](#diseño-y-arquitectura)
- [Instalación y Configuración](#instalación-y-configuración)
- [Estructura de Directorios](#estructura-de-directorios)

## Requisitos Técnicos

### Backend
- **Python**: 3.8+
- **Django**: 4.0.6+
- **Bases de datos**:
  - SQLite (por defecto)
  - Posibilidad de múltiples bases de datos por aplicación
- **Dependencias principales**:
  - django-allauth (autenticación social)
  - djangorestframework (APIs REST)
  - python-decouple (manejo de variables de entorno)
  - django-rest-framework-authtoken (autenticación por tokens)

### Frontend
- **Node.js**: 14+
- **npm** o **yarn** para gestión de dependencias
- **Tailwind CSS** para estilos
- **Configuración inicial excluida** del control de versiones

## Diseño y Arquitectura

### Estructura del Proyecto
- **Arquitectura limpia** con separación clara de responsabilidades
- **Sistema modular** con aplicaciones independientes
- **Frontend separado** en directorio `/frontend`

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
- **Configuración inicial** excluida del control de versiones
- **Estructura típica**:
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
5. Migrar las bases de datos:
   ```bash
   python manage.py migrate
   ```

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
src/
├── core_config/           # Configuración principal del proyecto
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── database_routers.py
├── core_auth/             # Aplicación de autenticación
│   ├── adapters/
│   ├── domain/
│   └── tests/
└── frontend/              # Frontend (ignorado en git)
    ├── package.json
    └── tailwind.config.js
```

## Consideraciones Importantes
1. **Variables de entorno**: Todas las configuraciones sensibles deben estar en `.env`
2. **Migraciones**: Cada aplicación puede tener su propia base de datos
3. **Frontend**: La configuración inicial debe ser recreada siguiendo las instrucciones
