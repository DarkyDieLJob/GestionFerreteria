"""Test settings for core_config."""

from .settings import *
import os

# Use in-memory databases for tests; preserve negocio_db alias from base settings
# Start from base settings.DATABASES so routers keep working
DATABASES = DATABASES.copy()
# Use a single file-based SQLite DB for all aliases to avoid separate in-memory connections
# Ensure data directory exists
_DATA_DIR = BASE_DIR / 'data'
os.makedirs(_DATA_DIR, exist_ok=True)
_TEST_DB_PATH = _DATA_DIR / 'test_default.sqlite3'
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': _TEST_DB_PATH,
    # Use the same file for the Django test database so the CI pre-migration step applies
    'TEST': {
        'NAME': _TEST_DB_PATH,
    },
}
# Alias other names to the same DB so using="negocio_db" etc. hit the same database
DATABASES['negocio_db'] = {**DATABASES['default'], 'TEST': {'MIRROR': 'default'}}
DATABASES['articles_db'] = {**DATABASES['default'], 'TEST': {'MIRROR': 'default'}}
DATABASES['cart_db'] = {**DATABASES['default'], 'TEST': {'MIRROR': 'default'}}

# Speed up password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable password validation for tests
AUTH_PASSWORD_VALIDATORS = []

# Disable logging for tests
import logging
logging.disable(logging.CRITICAL)

# Disable debug toolbar for tests
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'debug_toolbar']
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'debug_toolbar.middleware.DebugToolbarMiddleware']

# Keep INSTALLED_APPS from base settings as-is to use each app's AppConfig

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Email backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Staff-only coverage view toggle for local/testing environments.
# La vista /coverage/ sólo se habilita si DEBUG=True o si esta bandera está en True.
# En tests no es necesario habilitarla.
COVERAGE_VIEW_ENABLED = False

# Controlar uso de migraciones por variable de entorno
# Por defecto (local), se deshabilitan migraciones para acelerar tests.
# En CI, exportar USE_MIGRATIONS=1 para aplicar migraciones reales.
if os.getenv("USE_MIGRATIONS", "0") == "1":
    MIGRATION_MODULES = {}
else:
    class DisableMigrations(dict):
        def __contains__(self, item):
            return True
        def __getitem__(self, item):
            return None
    MIGRATION_MODULES = DisableMigrations()

# Deshabilitar routers de BD en tests para evitar que el ruteo a aliases no-default
# impida la creación de tablas vía syncdb en CI. Todas las operaciones usarán 'default'.
DATABASE_ROUTERS = []
