# templates/app_template/apps.py
from django.apps import AppConfig

class Core_authConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_auth'