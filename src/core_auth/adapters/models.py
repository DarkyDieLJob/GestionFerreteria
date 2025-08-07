# Archivo de modelos del adaptador
# templates/app_template/adapters/models.py
from django.db import models

class Core_auth(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_auth_items'