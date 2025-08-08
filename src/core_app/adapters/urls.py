from django.urls import path
from . import views

app_name = 'core_app'

urlpatterns = [
    #la ruta raiz se llama home
    path('', views.home, name='home'),
    # path('', views.article_list, name='article_list'),
]
