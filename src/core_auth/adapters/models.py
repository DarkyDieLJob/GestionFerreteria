# Archivo de modelos del adaptador
# templates/app_template/adapters/models.py
from django.db import models
from django.contrib.auth import get_user_model
import secrets
import string

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
    # Teléfono opcional del usuario (para facilitar contacto)
    phone_number = models.CharField(max_length=32, blank=True, default='')
    # Hash de los últimos 4 del DNI (dato de recuperación obligatorio)
    dni_last4_hash = models.CharField(max_length=255, blank=True, default='')
    # Hint no sensible para recordar al usuario el tipo de dato de recuperación
    recovery_hint = models.CharField(max_length=64, blank=True, default='Últimos 4 del DNI')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Perfil({self.user})"


class PasswordResetRequest(models.Model):
    """Cola de solicitudes de reseteo de contraseña (sin email)."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),              # creada por el usuario, pendiente de revisión
        ('under_review', 'Under review'),    # en revisión por staff
        ('ready_to_deliver', 'Ready'),       # temporal generada, lista para entregar
        ('resolved', 'Resolved'),            # entregada y activada
        ('expired', 'Expired'),              # vencida antes de entrega
        ('rejected', 'Rejected'),            # rechazada por inconsistencias
    )

    # Inputs provistos por el solicitante
    # Campo de compatibilidad: identificador ingresado por el usuario (usuario o email)
    # Algunos tests esperan este nombre de campo explícitamente.
    identifier_submitted = models.CharField(max_length=255, blank=True, default='')
    username_input = models.CharField(max_length=150, blank=True, default='')
    email_input = models.EmailField(blank=True, default='')
    dni_last4_provided = models.CharField(max_length=4, blank=True, default='')  # no almacenar si no es necesario, ideal comparar y descartar
    provided_phone = models.CharField(max_length=32, blank=True, default='')

    # Asociación tentativa y metadatos
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='password_reset_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    short_code = models.CharField(max_length=16, unique=True, editable=False, default='')
    notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default='')
    expires_at = models.DateTimeField(null=True, blank=True)

    # Gestión interna por staff
    processed_at = models.DateTimeField(null=True, blank=True, help_text='Cuando se generó la temporal')
    delivered_at = models.DateTimeField(null=True, blank=True, help_text='Cuando se activó y entregó al usuario')
    processed_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='processed_reset_requests')

    # Contraseña temporal (se genera pero no se activa hasta la entrega). Guardar solo hash; opcionalmente una vista previa en memoria.
    temp_password_hash = models.CharField(max_length=255, blank=True, default='')
    temp_password_preview = models.CharField(max_length=64, blank=True, default='', help_text='Se guarda sólo para mostrar al staff en pantalla (opcional).')

    def __str__(self) -> str:
        # Prefer the exact identifier submitted by the user if available
        base = (self.identifier_submitted or '').strip() or self.username_input or self.email_input or 'unknown'
        return f"PasswordResetRequest({base}, {self.status})"

    def save(self, *args, **kwargs):
        # Ensure short_code exists and is unique before first save
        if not self.short_code:
            alphabet = string.ascii_uppercase + string.digits
            for _ in range(10):  # try a few times to avoid rare collision
                candidate = ''.join(secrets.choice(alphabet) for _ in range(8))
                if not PasswordResetRequest.objects.filter(short_code=candidate).exists():
                    self.short_code = candidate
                    break
            if not self.short_code:
                # fallback
                self.short_code = ''.join(secrets.choice(alphabet) for _ in range(8))
        super().save(*args, **kwargs)