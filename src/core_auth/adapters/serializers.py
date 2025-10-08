# Archivo de serializadores del adaptador
# templates/app_template/adapters/serializers.py
from rest_framework import serializers
from .models import Core_auth

class Core_authSerializer(serializers.ModelSerializer):
    class Meta:
        model = Core_auth
        fields = '__all__'