from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse, Http404
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
    return HttpResponse(content, content_type='text/html')