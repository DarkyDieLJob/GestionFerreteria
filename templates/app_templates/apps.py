# templates/app_template/apps.py
from django.apps import AppConfig

class {{ app_name|capfirst }}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{{ app_name }}'