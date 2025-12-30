"""
Señales de la app `precios`.

Crea un registro `Descuento` por defecto tras aplicar migraciones
de la app `precios` en la base de datos `negocio_db`.

Nota: asegúrate de importar este módulo en el AppConfig de la app
(`ready()`) para que la señal se registre al iniciar Django.
"""

from decimal import Decimal

from django.apps import apps
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
    # Esto evita errores en CI/entornos donde solo existe 'default' y
    # aún no hay alias 'negocio_db' migrado.
    db_alias = kwargs.get("using") or "default"

    Descuento = apps.get_model("precios", "Descuento")
    # Crear o recuperar el descuento por defecto con valores predefinidos en la BD correspondiente
    Descuento.objects.using(db_alias).get_or_create(
        tipo="Sin Descuento",
        defaults={
            "efectivo": Decimal("0.10"),
            "bulto": Decimal("0.05"),
            "cantidad_bulto": 5,
            "general": Decimal("0.0"),
            "temporal": False,
        },
    )
