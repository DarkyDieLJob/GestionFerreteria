from django.conf import settings
from django.urls import reverse


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
