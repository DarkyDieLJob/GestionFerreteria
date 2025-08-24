# Archivo del repositorio del adaptador
# templates/app_template/adapters/repository.py
from django.db import connections
from .models import Core_app
from ..ports.interfaces import Core_appRepository


class DjangoCore_appRepository(Core_appRepository):
    def save(self, data):
        with connections["core_app_db"].cursor():
            Core_app.objects.using("core_app_db").create(**data)

    def get_all(self):
        with connections["core_app_db"].cursor():
            return Core_app.objects.using("core_app_db").all()
