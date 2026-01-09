from __future__ import annotations

# Inicializa la app de Celery cuando Django se carga
from .celery import app as celery_app  # noqa: F401

__all__ = ("celery_app",)
