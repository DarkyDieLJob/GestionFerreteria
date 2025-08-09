from django.urls import path
from . import views

app_name = 'core_auth'

urlpatterns = [
    # Autenticación
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # Recuperación sin email
    path('forgot/', views.ForgotPasswordInfoView.as_view(), name='forgot_password_info'),
    path('password/change/', views.PasswordChangeEnforcedView.as_view(), name='password_change_enforced'),
    # Staff: gestión de solicitudes
    path('staff/reset-requests/', views.ResetRequestListView.as_view(), name='staff_reset_requests'),
    path('staff/reset-requests/<int:pk>/', views.ResetRequestDetailView.as_view(), name='staff_reset_request_detail'),
    path('staff/reset-requests/<int:pk>/approve/', views.approve_reset_request, name='staff_reset_request_approve'),
]
