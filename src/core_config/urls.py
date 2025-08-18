"""core_config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from core_app.adapters.views import home, coverage_report, coverage_asset, coverage_raw

urlpatterns = [
    path('', home, name='home'),
    path('coverage/', coverage_report, name='coverage'),
    path('coverage/assets/<path:path>', coverage_asset, name='coverage_asset'),
    path('coverage/raw/<path:path>', coverage_raw, name='coverage_raw'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('auth/', include(('core_auth.adapters.urls', 'core_auth'), namespace='core_auth')),
    path('dashboard/', include('core_app.adapters.urls', namespace='core_app')),  # Para el dashboard genérico
    # URLs de la app articulos (vistas y formularios de búsqueda/mapeo)
    path('articulos/', include('articulos.urls')),
]

