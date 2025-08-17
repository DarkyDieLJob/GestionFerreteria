from django.apps import AppConfig

class ProveedoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'proveedores'

    def ready(self):
        # Importa los modelos ubicados en adapters para que Django los registre
        from . import adapters  # noqa: F401
        from .adapters import models as _models  # noqa: F401
