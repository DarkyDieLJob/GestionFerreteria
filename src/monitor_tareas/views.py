from __future__ import annotations

from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpRequest
from django.http import JsonResponse
import time
from django.views import View
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        user = getattr(self.request, "user", None)
        return bool(user and user.is_authenticated and user.is_staff)


@method_decorator(ensure_csrf_cookie, name="dispatch")
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
            # indicador para el template: si se quiere, puede renderizar placeholders
            "deferred_load": True,
        })
        return ctx


class TareasStatusView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """Entrega JSON con el estado de Celery (active/reserved/scheduled).

    Se usa para cargar asincrónicamente la información y no bloquear el renderizado
    inicial de la página.
    """

    # cache sencillo en memoria por proceso para evitar golpear Inspect demasiado seguido
    _cache_data = None
    _cache_ts = 0.0
    _cache_ttl_seconds = 2.0
    # Lista negra temporal para ocultar programadas revocadas inmediatamente (hasta que el worker propague estado)
    _revoked_blacklist: set[str] = set()

    def get(self, request: HttpRequest, *args, **kwargs):  # type: ignore[override]
        now = time.monotonic()
        if (now - self._cache_ts) < self._cache_ttl_seconds and self._cache_data is not None:
            return JsonResponse(self._cache_data)

        try:
            from celery.app.control import Inspect
            from core_config.celery import app as celery_app

            insp = Inspect(app=celery_app)
            active = insp.active() or {}
            reserved = insp.reserved() or {}
            scheduled = insp.scheduled() or {}
            # Filtrar programadas que ya estén revocadas para que no se muestren
            revoked_map = insp.revoked() or {}
            revoked_ids = set()
            for _w, ids in (revoked_map or {}).items():
                for tid in (ids or []):
                    revoked_ids.add(tid)
            # Unir con blacklist local (agregada cuando se presiona Forzar procesamiento)
            if self._revoked_blacklist:
                revoked_ids.update(self._revoked_blacklist)
            if revoked_ids:
                cleaned = {}
                for w, items in (scheduled or {}).items():
                    new_items = []
                    for it in (items or []):
                        req = it.get("request") or {}
                        if req.get("id") not in revoked_ids:
                            new_items.append(it)
                    cleaned[w] = new_items
                scheduled = cleaned
        except Exception:
            active = {}
            reserved = {}
            scheduled = {}

        data = {"active": active, "reserved": reserved, "scheduled": scheduled}
        self.__class__._cache_data = data
        self.__class__._cache_ts = now
        return JsonResponse(data)


class TareasTriggerNowView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request: HttpRequest, *args, **kwargs):  # type: ignore[override]
        try:
            from importaciones.tasks import procesar_pendientes_task
            from celery.app.control import Inspect
            from core_config.celery import app as celery_app
            from .views import TareasStatusView

            # Revocar tareas programadas del mismo tipo para evitar duplicados
            insp = Inspect(app=celery_app)
            scheduled = insp.scheduled() or {}
            revoked = 0
            for _worker, items in (scheduled or {}).items():
                for item in items or []:
                    req = item.get("request") or {}
                    if req.get("name") == "importaciones.procesar_pendientes":
                        task_id = req.get("id")
                        if task_id:
                            celery_app.control.revoke(task_id)
                            # añadir a blacklist local para ocultarlo inmediatamente en el JSON
                            TareasStatusView._revoked_blacklist.add(task_id)
                            revoked += 1

            # Encolar una nueva tarea inmediata
            result = procesar_pendientes_task.apply_async(countdown=0)
            # invalidar cache del status para reflejar el cambio en el próximo fetch
            TareasStatusView._cache_ts = 0.0
            TareasStatusView._cache_data = None
            return JsonResponse({"ok": True, "enqueued_id": str(result.id), "revoked_scheduled": revoked})
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=500)
