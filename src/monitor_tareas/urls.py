from django.urls import path
from .views import TareasListView, TareasStatusView, TareasTriggerNowView

app_name = "monitor_tareas"

urlpatterns = [
    path("", TareasListView.as_view(), name="list"),
    path("status/", TareasStatusView.as_view(), name="status"),
    path("trigger-now/", TareasTriggerNowView.as_view(), name="trigger_now"),
]
