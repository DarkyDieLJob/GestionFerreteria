# Pruebas para los adaptadores
# templates/app_template/tests/test_adapters.py
import pytest
from django.test import TestCase
from ..adapters.models import {{ app_name|capfirst }}

class {{ app_name|capfirst }}AdapterTests(TestCase):
    def test_{{ app_name }}_model(self):
        # Implementar pruebas para adaptadores
        pass