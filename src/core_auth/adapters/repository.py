# Archivo del repositorio del adaptador
# templates/app_template/adapters/repository.py
from django.db import connections
from .models import Core_auth
from ..ports.interfaces import Core_authRepository

class DjangoCore_authRepository(Core_authRepository):
    def save(self, data):
        with connections['core_auth_db'].cursor():
            Core_auth.objects.using('core_auth_db').create(**data)

    def get_all(self):
        with connections['core_auth_db'].cursor():
            return Core_auth.objects.using('core_auth_db').all()