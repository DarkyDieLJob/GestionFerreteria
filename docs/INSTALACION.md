# Guía de Instalación (Primer Clonado)

Esta guía describe el setup recomendado y alternativo para instalar y ejecutar el proyecto desde cero en Windows y Linux/macOS.

## 0) Setup rápido recomendado (Windows y Linux/macOS)

Usa los scripts de `scripts/` para automatizar: creación de venv, instalación de dependencias, creación de `src/.env`, configuración de Tailwind (frontend) y migraciones.

- Windows (PowerShell):
  ```powershell
  powershell -ExecutionPolicy Bypass -NoLogo -NoProfile -File .\scripts\setup.ps1 -Requirements notebook -Test
  ```
- Linux/macOS (bash):
  ```bash
  chmod +x ./scripts/setup.sh
  ./scripts/setup.sh --requirements notebook --test
  ```

Notas:
- `-Requirements`/`--requirements` acepta: `dev`, `notebook` (recomendado), `lista_v3` o una ruta a un archivo.
- `lista_v3` es un ejemplo heredado de otro proyecto; en este repositorio el archivo efectivo por defecto es `notebook.txt`.
- Para omitir frontend (Tailwind) agrega `-NoFrontend`/`--no-frontend`.
- Los scripts aseguran `djangorestframework` y `python-decouple` si faltan.

Al finalizar, levanta el servidor con:
```bash
# Linux/macOS
./venv/bin/python ./src/manage.py runserver

# Windows (PowerShell)
./venv/Scripts/python.exe ./src/manage.py runserver
```

> Nota: El archivo `manage.py` está dentro del directorio `src/`.

### Comandos rápidos

- Windows (PowerShell):
  ```powershell
  # Setup automatizado con pruebas
  powershell -ExecutionPolicy Bypass -NoLogo -NoProfile -File .\scripts\setup.ps1 -Requirements notebook -Test
  # Ejecutar servidor
  ./venv/Scripts/python.exe ./src/manage.py runserver
  # Ejecutar tests
  ./venv/Scripts/python.exe -m pytest -q
  # Crear superusuario
  ./venv/Scripts/python.exe ./src/manage.py createsuperuser
  ```

- Linux/macOS (bash):
  ```bash
  # Setup automatizado con pruebas
  ./scripts/setup.sh --requirements notebook --test
  # Ejecutar servidor
  ./venv/bin/python ./src/manage.py runserver
  # Ejecutar tests
  ./venv/bin/python -m pytest -q
  # Crear superusuario
  ./venv/bin/python ./src/manage.py createsuperuser
  ```

## 1) Prerrequisitos (para setup manual)

- Git instalado
- Python 3.9+ instalado (verifica con `python3 --version`)
- Pip instalado (`python3 -m ensurepip --upgrade`)
- Recomendado: virtualenv (opcional si usas `python -m venv`)

## 2) Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd DjangoProyects
```

## 3) Crear y activar entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

Para salir del entorno virtual posteriormente: `deactivate`

## 4) Instalar dependencias

El proyecto organiza dependencias en `requirements/`.
Opciones comunes: `notebook.txt` (recomendado/efectivo), `dev.txt` (desarrollo), `lista_v3.txt` (ejemplo heredado de otro proyecto).

```bash
pip install -r requirements/notebook.txt
# opcional según tu caso
# pip install -r requirements/dev.txt
# pip install -r requirements/lista_v3.txt
```

Si falla alguna dependencia, asegúrate de tener herramientas de compilación básicas (ej.: `build-essential`, `python3-dev`).

## 5) Configurar variables de entorno (.env)

Crea un archivo `.env` en `src/` (misma carpeta donde está `manage.py`):

```bash
cat > src/.env << 'EOF'
# Django
SECRET_KEY=changeme_super_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Base de datos (por defecto SQLite)
# Si usas otras DB, configura aquí las credenciales correspondientes.

# Social auth (si aplica)
GITHUB_CLIENT_ID=
GITHUB_SECRET=
EOF
```

Ajusta los valores según tu entorno.

## 6) Migraciones de base de datos

Ejecuta los comandos desde `src/` porque ahí está `manage.py`:

```bash
cd src
python manage.py migrate
```

## 7) (Opcional) Crear superusuario

```bash
python manage.py createsuperuser
```

Completa los datos cuando se te soliciten.

## 8) Ejecutar el servidor de desarrollo

Asegúrate de que el entorno virtual está activo y que estás en `src/`:

```bash
python manage.py runserver
```

Abre en el navegador: http://127.0.0.1:8000/

## 9) Ejecutar pruebas automatizadas

Las pruebas viven bajo `src/`. Desde la raíz del repo:

```bash
source venv/bin/activate
cd src
python -m pytest -q
```

Deberías ver todos los tests en verde. Si quieres reporte detallado, quita `-q`.

## 10) Verificar funcionalidades básicas

- Acceso a la página principal: http://127.0.0.1:8000/
- Registro/Login/Logout desde las vistas de autenticación
- Panel de admin (si creaste superusuario): http://127.0.0.1:8000/admin/

## 11) Frontend (Tailwind)

Los scripts crean `frontend/` y compilan Tailwind a `static/css/tailwind.css`. Si hiciste setup manual, puedes crear el frontend así:

```bash
# desde la raíz
mkdir -p frontend/src static/css
cat > frontend/package.json << 'EOF'
{
  "name": "django-frontend",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "dev": "tailwindcss -i ./src/input.css -o ../static/css/tailwind.css -w",
    "build": "tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.10"
  }
}
EOF

cat > frontend/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../src/**/*.html",
    "../src/**/templates/**/*.html",
    "../templates/**/*.html"
  ],
  theme: { extend: {} },
  plugins: [],
};
EOF

cat > frontend/postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
EOF

cat > frontend/src/input.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

cd frontend
npm install
npx tailwindcss -i ./src/input.css -o ../static/css/tailwind.css --minify
```

## 12) Solución de problemas comunes

- "command not found: python": usa `python3` y `pip3` según tu distro.
- Error de dependencias nativas: instala herramientas de compilación (Ubuntu/Debian: `sudo apt-get install build-essential python3-dev`).
- Variables de entorno no cargan: confirma que el `.env` está en `src/` y que `DEBUG`/`SECRET_KEY` tienen valores válidos.
- No se genera CSS de Tailwind: verifica que Node/npm estén instalados y corre `npm install && npm run build` en `frontend/`.
- Errores de migración: elimina `db.sqlite3` (si usas SQLite) y la carpeta de migraciones de apps específicas como último recurso, luego vuelve a `python manage.py migrate`.

## 12) Resumen del algoritmo

1. Clonar repo y entrar al directorio
2. Crear/activar `venv`
3. `pip install -r requirements.txt`
4. Crear `src/.env`
5. `cd src && python manage.py migrate`
6. (Opcional) `python manage.py createsuperuser`
7. `python manage.py runserver`
8. (Opcional) `python -m pytest -q`

Con estos pasos, el proyecto queda funcional desde un clonado limpio.
