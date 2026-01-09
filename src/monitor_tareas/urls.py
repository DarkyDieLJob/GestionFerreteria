from django.urls import path
from .views import TareasListView

app_name = "monitor_tareas"

urlpatterns = [
    path("", TareasListView.as_view(), name="list"),
]
