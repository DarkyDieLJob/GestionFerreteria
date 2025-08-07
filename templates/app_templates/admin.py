# templates/app_template/admin.py
from django.contrib import admin
from .adapters.models import {{ app_name|capfirst }}

admin.site.register({{ app_name|capfirst }})