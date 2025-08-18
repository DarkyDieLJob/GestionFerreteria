from django.apps import AppConfig


class PreciosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'precios'

    def ready(self):
        # Registrar modelos ubicados en adapters
        from . import adapters  # noqa: F401
        from .adapters import models as _models  # noqa: F401
        # Conectar señales de la app (post_migrate para Descuento por defecto)
        import precios.signals  # noqa: F401
