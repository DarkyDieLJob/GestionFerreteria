# templates/app_template/apps.py
from django.apps import AppConfig


class Core_authConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core_auth"

    def ready(self):
        # Importar señales para asegurar creación de perfil
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Evitar romper el arranque si hay problemas de import en migraciones tempranas
            pass
