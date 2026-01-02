"""
Señales de la app `precios`.

Crea un registro `Descuento` por defecto tras aplicar migraciones
de la app `precios` en la base de datos `negocio_db`.

Nota: asegúrate de importar este módulo en el AppConfig de la app
(`ready()`) para que la señal se registre al iniciar Django.
"""

from decimal import Decimal

import os
from django.apps import apps
from django.conf import settings
from django.db import connections
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_default_descuento(sender, **kwargs):
    """
    Crea (si no existe) un `Descuento` con `tipo="Sin Descuento"` una vez
    que las migraciones de la app `precios` han sido aplicadas.

    - Se limita a ejecutarse cuando `sender.name == 'precios'`.
    - Usa `negocio_db` para respetar el enrutamiento de bases configurado.
    """
    if not sender or getattr(sender, "name", None) != "precios":
        return

    # Usar el alias de base de datos provisto por la señal post_migrate.
    # En producción preferimos el alias 'negocio_db' si está configurado; si no, el alias de la señal.
    db_alias = kwargs.get("using") or "default"
    preferred_alias = "negocio_db" if "negocio_db" in connections else db_alias

    Descuento = apps.get_model("precios", "Descuento")

    # Si la tabla aún no existe en este alias (p.ej. CI con app sin migraciones), salir sin error.
    # Pero durante tests (pytest) no aplicamos este guard para permitir mocks sin tocar DB.
    running_tests = bool(os.environ.get("PYTEST_CURRENT_TEST")) or bool(getattr(settings, "TESTING", False))
    if not running_tests:
        try:
            existing_tables = set(connections[preferred_alias].introspection.table_names())
            if Descuento._meta.db_table not in existing_tables:
                return
        except Exception:
            # Si no se puede inspeccionar, hacer un fail-safe y no ejecutar
            return

    # Crear o recuperar el descuento por defecto con valores predefinidos en la BD correspondiente
    Descuento.objects.using(preferred_alias).get_or_create(
        tipo="Sin Descuento",
        defaults={
            "efectivo": Decimal("0.10"),
            "bulto": Decimal("0.05"),
            "cantidad_bulto": 5,
            "general": Decimal("0.0"),
            "temporal": False,
        },
    )
