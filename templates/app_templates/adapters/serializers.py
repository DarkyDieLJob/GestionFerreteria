# Archivo de serializadores del adaptador
# templates/app_template/adapters/serializers.py
from rest_framework import serializers
from .models import {{ app_name|capfirst }}

class {{ app_name|capfirst }}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {{ app_name|capfirst }}
        fields = '__all__'