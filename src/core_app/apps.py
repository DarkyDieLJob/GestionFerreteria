# templates/app_template/apps.py
from django.apps import AppConfig

class Core_appConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_app'