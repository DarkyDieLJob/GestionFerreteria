# templates/app_template/admin.py
from django.contrib import admin
from .adapters.models import Core_app

admin.site.register(Core_app)
