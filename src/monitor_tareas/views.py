from __future__ import annotations

from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpRequest


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        user = getattr(self.request, "user", None)
        return bool(user and user.is_authenticated and user.is_staff)


class TareasListView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "monitor_tareas/list.html"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        ctx = super().get_context_data(**kwargs)
        # Intentar consultar el estado de Celery vía inspect. Si falla, mostrar vacío.
        try:
            from celery.app.control import Inspect
            from core_config.celery import app as celery_app

            insp = Inspect(app=celery_app)
            active = insp.active() or {}
            reserved = insp.reserved() or {}
            scheduled = insp.scheduled() or {}
        except Exception:
            active = {}
            reserved = {}
            scheduled = {}

        ctx.update({
            "active": active,
            "reserved": reserved,
            "scheduled": scheduled,
        })
        return ctx
