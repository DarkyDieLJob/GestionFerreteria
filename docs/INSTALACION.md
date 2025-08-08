# Guía de Instalación (Primer Clonado)

Esta guía está pensada como un algoritmo paso a paso para que un agente (o cualquier persona) pueda instalar y ejecutar el proyecto desde cero en Linux.

> Nota: El archivo `manage.py` está dentro del directorio `src/`.

## 0) Prerrequisitos

- Git instalado
- Python 3.10+ instalado (verifica con `python3 --version`)
- Pip instalado (`python3 -m ensurepip --upgrade`)
- Recomendado: virtualenv (opcional si usas `python -m venv`)

## 1) Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd DjangoProyects
```

## 2) Crear y activar entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

Para salir del entorno virtual posteriormente: `deactivate`

## 3) Instalar dependencias

```bash
pip install -r requirements.txt
```

Si falla alguna dependencia, asegúrate de tener herramientas de compilación básicas (ej.: `build-essential`, `python3-dev`).

## 4) Configurar variables de entorno (.env)

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

## 5) Migraciones de base de datos

Ejecuta los comandos desde `src/` porque ahí está `manage.py`:

```bash
cd src
python manage.py migrate
```

## 6) (Opcional) Crear superusuario

```bash
python manage.py createsuperuser
```

Completa los datos cuando se te soliciten.

## 7) Ejecutar el servidor de desarrollo

Asegúrate de que el entorno virtual está activo y que estás en `src/`:

```bash
python manage.py runserver
```

Abre en el navegador: http://127.0.0.1:8000/

## 8) Ejecutar pruebas automatizadas

Las pruebas viven bajo `src/`. Desde la raíz del repo:

```bash
source venv/bin/activate
cd src
python -m pytest -q
```

Deberías ver todos los tests en verde. Si quieres reporte detallado, quita `-q`.

## 9) Verificar funcionalidades básicas

- Acceso a la página principal: http://127.0.0.1:8000/
- Registro/Login/Logout desde las vistas de autenticación
- Panel de admin (si creaste superusuario): http://127.0.0.1:8000/admin/

## 10) (Opcional) Frontend

Si decides usar el frontend opcional (Tailwind u otros):

```bash
cd frontend
npm install
npm run dev
# o
# yarn
yarn dev
```

## 11) Solución de problemas comunes

- "command not found: python": usa `python3` y `pip3` según tu distro.
- Error de dependencias nativas: instala herramientas de compilación (Ubuntu/Debian: `sudo apt-get install build-essential python3-dev`).
- Variables de entorno no cargan: confirma que el `.env` está en `src/` y que `DEBUG`/`SECRET_KEY` tienen valores válidos.
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
