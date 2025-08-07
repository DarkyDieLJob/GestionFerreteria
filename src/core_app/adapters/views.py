# Archivo de vistas del adaptador
# templates/app_template/adapters/views.py
from django.shortcuts import render
from .models import Core_app

def core_app_list(request):
    items = Core_app.objects.using('core_app_db').all()
    return render(request, 'core_app/core_app_list.html', {'items': items})