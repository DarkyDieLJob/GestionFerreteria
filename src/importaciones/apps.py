from django.apps import AppConfig


class ImportacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'importaciones'

    def ready(self):
        # Registrar modelos ubicados en adapters
        from . import adapters  # noqa: F401
        from .adapters import models as _models  # noqa: F401
