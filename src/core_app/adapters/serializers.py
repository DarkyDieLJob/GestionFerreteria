# Archivo de serializadores del adaptador
# templates/app_template/adapters/serializers.py
from rest_framework import serializers
from .models import Core_app


class Core_appSerializer(serializers.ModelSerializer):
    class Meta:
        model = Core_app
        fields = "__all__"
