# templates/app_template/admin.py
from django.contrib import admin
from .adapters.models import Core_auth

admin.site.register(Core_auth)