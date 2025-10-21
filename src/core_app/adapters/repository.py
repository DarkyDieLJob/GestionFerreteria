# Archivo del repositorio del adaptador
# templates/app_template/adapters/repository.py
from .models import Core_app
from ..ports.interfaces import Core_appRepository


class DjangoCore_appRepository(Core_appRepository):
    def save(self, data):
        Core_app.objects.create(**data)

    def get_all(self):
        return Core_app.objects.all()