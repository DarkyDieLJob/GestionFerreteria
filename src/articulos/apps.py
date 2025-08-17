from django.apps import AppConfig


class ArticulosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'articulos'

    def ready(self):
        # Asegura el registro de modelos ubicados en adapters
        from . import adapters  # noqa: F401
        from .adapters import models as _models  # noqa: F401
