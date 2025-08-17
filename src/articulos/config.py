from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE = {
    'negocio_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'data' / 'negocio.sqlite3'),
    }
}
# Configuración de la base de datos específica de la app