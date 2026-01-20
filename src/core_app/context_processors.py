from django.conf import settings
from django.urls import reverse
import os
import re


def _truthy(val, default=False):
    if val is None:
        return default
    s = str(val).strip().lower()
    return s in {"1", "true", "yes", "on"}


def coverage(request):
    """
    Adds coverage report availability and URL to the template context.
    coverage_available mirrors the logic used by the view: enabled when DEBUG is True
    or when COVERAGE_VIEW_ENABLED setting is truthy.
    """
    enabled = bool(getattr(settings, "DEBUG", False) or getattr(settings, "COVERAGE_VIEW_ENABLED", False))
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
            m = re.search(r"^#{2,3}\s*(?:\[)?v?(\d+\.\d+\.\d+)(?:\])?\b", content, re.MULTILINE)
            if m:
                version = m.group(1)
        except Exception:
            version = "dev"

    return {
        "app_name": app_name,
        "app_version": version,
    }


def ui_meta(request):
    """
    Combina metadatos de branding del hijo y atribución del padre con toggles de visibilidad.
    Expone:
      - app_name, app_version
      - template_name, template_version
      - show_project_version, show_template_attrib, template_attrib_minimal,
        show_template_version_in_nav, show_footer_year
    Prioridades:
      - app_version: ENV APP_VERSION > CHANGELOG.md > 'dev'
      - template_*: template_meta constants > fallbacks
      - toggles: ENV overrides > settings attributes > defaults
    """
    # Hijo
    app_name = getattr(settings, "NOMBRE_APLICACION", "Mi Aplicacion")

    # Reusar lógica de app_meta para versión, priorizando ENV
    env_app_version = os.getenv("APP_VERSION")
    if env_app_version:
        app_version = env_app_version
    else:
        # Buscar en CHANGELOG como fallback
        base_dir = getattr(settings, "BASE_DIR", None)
        changelog_path = None
        if base_dir:
            repo_root = os.path.abspath(os.path.join(base_dir, os.pardir))
            candidate = os.path.join(repo_root, "CHANGELOG.md")
            if os.path.exists(candidate):
                changelog_path = candidate
        app_version = "dev"
        if changelog_path:
            try:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    content = f.read()
                m = re.search(r"^#{2,3}\s*(?:\[)?v?(\d+\.\d+\.\d+)(?:\])?\b", content, re.MULTILINE)
                if m:
                    app_version = m.group(1)
            except Exception:
                app_version = "dev"

    # Padre (plantilla)
    template_name = "DjangoProyects"
    template_version = "unknown"
    try:
        from template_meta import TEMPLATE_NAME, TEMPLATE_VERSION  # type: ignore

        if TEMPLATE_NAME:
            template_name = TEMPLATE_NAME
        if TEMPLATE_VERSION:
            template_version = TEMPLATE_VERSION
    except Exception:
        pass

    # Toggles (ENV > settings > defaults)
    show_project_version = _truthy(
        os.getenv("SHOW_PROJECT_VERSION", getattr(settings, "SHOW_PROJECT_VERSION", True)), True
    )
    show_template_attrib = _truthy(
        os.getenv("SHOW_TEMPLATE_ATTRIB", getattr(settings, "SHOW_TEMPLATE_ATTRIB", True)), True
    )
    template_attrib_minimal = _truthy(
        os.getenv("TEMPLATE_ATTRIB_MINIMAL", getattr(settings, "TEMPLATE_ATTRIB_MINIMAL", False)), False
    )
    show_template_version_in_nav = _truthy(
        os.getenv(
            "SHOW_TEMPLATE_VERSION_IN_NAV", getattr(settings, "SHOW_TEMPLATE_VERSION_IN_NAV", False)
        ),
        False,
    )
    show_footer_year = _truthy(
        os.getenv("SHOW_FOOTER_YEAR", getattr(settings, "SHOW_FOOTER_YEAR", True)), True
    )

    return {
        "app_name": app_name,
        "app_version": app_version,
        "template_name": template_name,
        "template_version": template_version,
        "show_project_version": show_project_version,
        "show_template_attrib": show_template_attrib,
        "template_attrib_minimal": template_attrib_minimal,
        "show_template_version_in_nav": show_template_version_in_nav,
        "show_footer_year": show_footer_year,
    }
