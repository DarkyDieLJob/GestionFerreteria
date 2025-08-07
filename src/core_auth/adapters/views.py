# Archivo de vistas del adaptador
# templates/app_template/adapters/views.py
from django.shortcuts import render
from .models import Core_auth

def core_auth_list(request):
    items = Core_auth.objects.using('core_auth_db').all()
    return render(request, 'core_auth/core_auth_list.html', {'items': items})