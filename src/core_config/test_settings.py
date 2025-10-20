"""Test settings for core_config."""

from .settings import *

# Use in-memory databases for tests; preserve negocio_db alias from base settings
# Start from base settings.DATABASES so routers keep working
DATABASES = DATABASES.copy()
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
}
# Ensure negocio_db mirrors default so migrations seeding default tables apply
DATABASES['negocio_db'] = DATABASES['default'].copy()
DATABASES['negocio_db']['TEST'] = {'MIRROR': 'default'}

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
