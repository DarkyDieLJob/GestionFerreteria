# Archivo del repositorio del adaptador
# templates/app_template/adapters/repository.py
from django.db import connections
from .models import {{ app_name|capfirst }}
from ..ports.interfaces import {{ app_name|capfirst }}Repository

class Django{{ app_name|capfirst }}Repository({{ app_name|capfirst }}Repository):
    def save(self, data):
        with connections['{{ app_name }}_db'].cursor():
            {{ app_name|capfirst }}.objects.using('{{ app_name }}_db').create(**data)

    def get_all(self):
        with connections['{{ app_name }}_db'].cursor():
            return {{ app_name|capfirst }}.objects.using('{{ app_name }}_db').all()