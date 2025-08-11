from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse, Http404, FileResponse
from pathlib import Path
from .models import Core_app

@login_required
def home(request):
    """
    Vista de inicio que muestra un mensaje de bienvenida con los datos del usuario.
    Requiere que el usuario esté autenticado.
    """
    user = request.user
    context = {
        'user': user,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'last_login': user.last_login,
        'date_joined': user.date_joined,
    }
    return render(request, 'core_app/home.html', context)


def terms(request):
    """
    Vista pública que renderiza los Términos de Servicio.
    No requiere autenticación y muestra contenido estático.
    """
    return render(request, 'core_app/terms.html')


def privacy(request):
    """
    Vista pública que renderiza la Política de Privacidad.
    No requiere autenticación y muestra contenido estático.
    """
    return render(request, 'core_app/privacy.html')


@staff_member_required
def coverage_report(request):
    """
    Vista solo para staff que sirve el reporte HTML de cobertura generado en htmlcov/index.html.
    Por defecto solo está disponible si DEBUG=True o si COVERAGE_VIEW_ENABLED=True en settings.
    """
    enabled = getattr(settings, 'COVERAGE_VIEW_ENABLED', None)
    if enabled is None:
        # Si no está definido explícitamente, permitir solo en DEBUG
        enabled = getattr(settings, 'DEBUG', False)

    if not enabled:
        raise Http404("Coverage report not available")

    # htmlcov vive en la raíz del repo cuando se ejecuta pytest desde la raíz.
    # BASE_DIR suele apuntar a src/, por lo que subimos un nivel.
    base_dir = Path(getattr(settings, 'BASE_DIR', Path(__file__).resolve().parent.parent))
    report_path = (base_dir.parent / 'htmlcov' / 'index.html').resolve()

    if not report_path.exists():
        raise Http404("Coverage report not found. Ejecuta pytest para generar htmlcov/")

    content = report_path.read_text(encoding='utf-8')
    # Inyectamos una etiqueta <base> para que los enlaces relativos (CSS/JS/otras páginas)
    # apunten a /coverage/raw/
    if '<base ' not in content:
        content = content.replace('<head>', '<head>\n  <base href="/coverage/raw/">', 1)
    return HttpResponse(content, content_type='text/html')


@staff_member_required
def coverage_asset(request, path: str):
    """
    Sirve archivos estáticos generados por coverage dentro de htmlcov/ (CSS/JS/imagenes),
    protegido para staff y sólo si la vista está habilitada (DEBUG o COVERAGE_VIEW_ENABLED=True).
    """
    enabled = getattr(settings, 'COVERAGE_VIEW_ENABLED', None)
    if enabled is None:
        enabled = getattr(settings, 'DEBUG', False)
    if not enabled:
        raise Http404("Coverage assets not available")

    base_dir = Path(getattr(settings, 'BASE_DIR', Path(__file__).resolve().parent.parent))
    htmlcov_dir = (base_dir.parent / 'htmlcov').resolve()

    # Normalizamos la ruta solicitada y evitamos path traversal
    requested = (htmlcov_dir / path).resolve()
    try:
        # asegurar que requested esté dentro de htmlcov_dir
        requested.relative_to(htmlcov_dir)
    except ValueError:
        raise Http404("Invalid path")

    if not requested.exists() or not requested.is_file():
        raise Http404("Asset not found")

    return FileResponse(open(requested, 'rb'))


@staff_member_required
def coverage_raw(request, path: str):
    """
    Sirve cualquier archivo dentro de htmlcov/ (incluye otras páginas HTML enlazadas desde index.html).
    Protegido y sólo disponible si la vista está habilitada.
    """
    enabled = getattr(settings, 'COVERAGE_VIEW_ENABLED', None)
    if enabled is None:
        enabled = getattr(settings, 'DEBUG', False)
    if not enabled:
        raise Http404("Coverage raw not available")

    base_dir = Path(getattr(settings, 'BASE_DIR', Path(__file__).resolve().parent.parent))
    htmlcov_dir = (base_dir.parent / 'htmlcov').resolve()
    requested = (htmlcov_dir / path).resolve()
    try:
        requested.relative_to(htmlcov_dir)
    except ValueError:
        raise Http404("Invalid path")
    if not requested.exists() or not requested.is_file():
        raise Http404("File not found")
    return FileResponse(open(requested, 'rb'))