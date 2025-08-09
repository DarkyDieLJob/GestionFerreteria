# Archivo de modelos del adaptador
# templates/app_template/adapters/models.py
from django.db import models
from django.contrib.auth import get_user_model

class Core_auth(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'core_auth_items'


class CoreAuthProfile(models.Model):
    """Perfil extendido para usuarios, usado para forzar cambio de contraseña."""
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='core_profile')
    must_change_password = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Perfil({self.user})"


class PasswordResetRequest(models.Model):
    """Cola de solicitudes de reseteo de contraseña (sin email)."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processed', 'Processed'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='password_reset_requests')
    identifier_submitted = models.CharField(max_length=255, help_text='Username o email ingresado por el solicitante')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default='')

    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='processed_reset_requests')
    temp_password_preview = models.CharField(max_length=64, blank=True, default='', help_text='Se guarda sólo para mostrar al staff en pantalla (opcional).')

    def __str__(self) -> str:
        base = self.identifier_submitted
        return f"PasswordResetRequest({base}, {self.status})"