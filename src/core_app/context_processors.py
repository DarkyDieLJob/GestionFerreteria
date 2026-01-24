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


def modes(request):
    project_mode = getattr(settings, "PROJECT_MODE", "local")
    tablet_mode = bool(getattr(settings, "TABLET_MODE", False))
    return {
        "PROJECT_MODE": project_mode,
        "TABLET_MODE": tablet_mode,
    }


def ui_meta(request):
    """
    Provee metadatos de UI esperados por tests y plantillas heredadas.
    - app_name: desde settings.NOMBRE_APLICACION (fallback: 'Mi Aplicacion')
    - app_version: APP_VERSION (env) o primera versión encontrada en CHANGELOG.md
    - template_name/template_version: desde src/template_meta.py
    - toggles: SHOW_* con defaults y override por env
    """

    def _truthy(value: str, default: bool) -> bool:
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    app_name = getattr(settings, "NOMBRE_APLICACION", "Mi Aplicacion")

    # Version de la app: APP_VERSION o CHANGELOG.md como en app_meta
    app_version = os.environ.get("APP_VERSION")
    if not app_version:
        version = "dev"
        base_dir = getattr(settings, "BASE_DIR", None)
        changelog_path = None
        if base_dir:
            repo_root = os.path.abspath(os.path.join(base_dir, os.pardir))
            candidate = os.path.join(repo_root, "CHANGELOG.md")
            if os.path.exists(candidate):
                changelog_path = candidate
        if changelog_path:
            try:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    content = f.read()
                m = re.search(
                    r"^#{2,3}\s*(?:\[)?v?(\d+\.\d+\.\d+)(?:\])?\b",
                    content,
                    re.MULTILINE,
                )
                if m:
                    version = m.group(1)
            except Exception:
                version = "dev"
        app_version = version

    # Datos de plantilla
    try:
        import template_meta  # type: ignore

        template_name = getattr(template_meta, "TEMPLATE_NAME", "")
        template_version = getattr(template_meta, "TEMPLATE_VERSION", "")
    except Exception:
        template_name = ""
        template_version = ""

    # Toggles con defaults del padre
    show_project_version = _truthy(os.environ.get("SHOW_PROJECT_VERSION"), default=True)
    show_template_attrib = _truthy(os.environ.get("SHOW_TEMPLATE_ATTRIB"), default=True)
    template_attrib_minimal = _truthy(
        os.environ.get("TEMPLATE_ATTRIB_MINIMAL"), default=False
    )
    show_template_version_in_nav = _truthy(
        os.environ.get("SHOW_TEMPLATE_VERSION_IN_NAV"), default=False
    )
    show_footer_year = _truthy(os.environ.get("SHOW_FOOTER_YEAR"), default=True)

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
