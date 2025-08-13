# Archivo de vistas del adaptador
# templates/app_template/adapters/views.py
from django.shortcuts import render
from .models import {{ app_name|capfirst }}

def {{ app_name }}_list(request):
    items = {{ app_name|capfirst }}.objects.using('{{ app_name }}_db').all()
    return render(request, '{{ app_name }}/{{ app_name }}_list.html', {'items': items})