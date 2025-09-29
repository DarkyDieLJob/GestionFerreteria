from django.conf import settings
from django.urls import reverse
import os
import re


def coverage(request):
    """
    Adds coverage report availability and URL to the template context.
    coverage_available mirrors the logic used by the view: enabled when DEBUG is True
    or when COVERAGE_VIEW_ENABLED setting is truthy.
    """
    enabled = bool(
        getattr(settings, "DEBUG", False)
        or getattr(settings, "COVERAGE_VIEW_ENABLED", False)
    )
    context = {
        "coverage_available": enabled,
        "coverage_url": None,
    }
    if enabled:
        try:
            context["coverage_url"] = reverse("core_app:coverage")
        except Exception:
            context["coverage_url"] = None
    return context


def app_meta(request):
    """
    Expone en el contexto:
    - app_name: tomado de settings.NOMBRE_APLICACION (fallback: 'Mi Aplicacion')
    - app_version: tomado de la primera versión encontrada en CHANGELOG.md (fallback: 'dev')

    Formatos soportados en CHANGELOG.md para encabezados de versión:
    - ## [1.0.0] - YYYY-MM-DD
    - ## 1.0.0
    - ## v1.0.0
    - ### [1.0.0] (YYYY-MM-DD)  # standard-version
    """
    app_name = getattr(settings, "NOMBRE_APLICACION", "Mi Aplicacion")

    # Resolver ruta a CHANGELOG.md en la raíz del repo (un nivel arriba de BASE_DIR de src)
    base_dir = getattr(settings, "BASE_DIR", None)
    changelog_path = None
    if base_dir:
        repo_root = os.path.abspath(os.path.join(base_dir, os.pardir))
        candidate = os.path.join(repo_root, "CHANGELOG.md")
        if os.path.exists(candidate):
            changelog_path = candidate

    version = "dev"
    if changelog_path:
        try:
            with open(changelog_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Buscar primera coincidencia de encabezado de versión
            # Soporta H2/H3 (## o ###), con o sin 'v', con o sin corchetes, p.ej:
            #   ## v1.2.0
            #   ## 1.2.0
            #   ## [1.2.0]
            #   ### [1.2.1] (YYYY-MM-DD)  <- standard-version
            m = re.search(
                r"^#{2,3}\s*(?:\[)?v?(\d+\.\d+\.\d+)(?:\])?\b", content, re.MULTILINE
            )
            if m:
                version = m.group(1)
        except Exception:
            version = "dev"

    return {
        "app_name": app_name,
        "app_version": version,
    }
