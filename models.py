from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.apps import apps
import uuid



# Crear descuento base tras migraciones
def create_default_descuento():
    try:
        Descuento = apps.get_model('precios', 'Descuento')
        if Descuento is None:
            return
        Descuento.objects.get_or_create(
            tipo="Sin Descuento",
            defaults={
                'efectivo': 0.10,
                'bulto': 0.05,
                'cantidad_bulto': 5,
                'general': 0.0,
                'temporal': False
            }
        )
    except Exception:
        # puede fallar en fases tempranas de migración; ignorar
        pass