from django.urls import path
from . import views

app_name = "core_app"

urlpatterns = [
    # la ruta raiz se llama home
    path("", views.home, name="home"),
    path("coverage/", views.coverage_report, name="coverage"),
    path("coverage/assets/<path:path>", views.coverage_asset, name="coverage_asset"),
    path("coverage/raw/<path:path>", views.coverage_raw, name="coverage_raw"),
    # vistas públicas estáticas
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
]
