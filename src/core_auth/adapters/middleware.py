from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

EXEMPT_PATH_NAMES = {
    "core_auth:password_change_enforced",
    "core_auth:logout",
    "core_auth:login",
}

EXEMPT_PATH_PREFIXES = (
    "/admin",
    "/static",
)


class ForcePasswordChangeMiddleware(MiddlewareMixin):
    """Si el usuario debe cambiar su contraseña, forzar redirección a la vista de cambio."""

    def process_request(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        # Excluir rutas específicas y prefijos
        path = request.path
        for prefix in EXEMPT_PATH_PREFIXES:
            if path.startswith(prefix):
                return None

        try:
            # Resolver nombres exentos por nombre de URL
            from django.urls import resolve

            match = resolve(path)
            if f"{match.namespace}:{match.url_name}" in EXEMPT_PATH_NAMES:
                return None
        except Exception:
            pass

        profile = getattr(user, "core_profile", None)
        if profile and profile.must_change_password:
            return redirect(reverse("core_auth:password_change_enforced"))

        return None
