from django.contrib import admin
from django.apps import apps

# Registrar automáticamente todos los modelos de la app "importaciones"
app_config = apps.get_app_config("importaciones")
for model in app_config.get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:  # pragma: no cover - idempotencia
        pass
