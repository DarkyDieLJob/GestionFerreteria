import logging
import secrets
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import login, logout, update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

# Set up logging
logger = logging.getLogger(__name__)

from .forms import RegisterForm, LoginForm, ResetRequestForm, EnforcedPasswordChangeForm
from .models import CoreAuthProfile, PasswordResetRequest
from .repository import DjangoAuthRepository
from ..domain.use_cases import RegisterUserUseCase, LoginUserUseCase, LogoutUserUseCase


auth_repository = DjangoAuthRepository()


class RegisterView(View):
    """
    Vista para el registro de nuevos usuarios.
    """
    template_name = 'core_auth/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('core_auth:login')
    
    def get(self, request, *args, **kwargs):
        """Muestra el formulario de registro."""
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        """Procesa el formulario de registro."""
        # Aceptar también 'password' como alias para password1/password2 (compatibilidad con pruebas)
        if 'password' in request.POST and 'password1' not in request.POST:
            data = request.POST.copy()
            data['password1'] = request.POST['password']
            data['password2'] = request.POST['password']
            form = self.form_class(data)
        else:
            form = self.form_class(request.POST)
        
        if form.is_valid():
            try:
                # Verificar si el correo ya existe (manualmente para manejar el error específico)
                from django.contrib.auth import get_user_model
                User = get_user_model()
                if User.objects.filter(email__iexact=form.cleaned_data['email']).exists():
                    form.add_error('email', 'Ya existe un usuario con este correo electrónico')
                    return render(request, self.template_name, {'form': form}, status=200)
                
                # Ejecutar el caso de uso de registro
                use_case = RegisterUserUseCase(auth_repository)
                user = use_case.execute(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password1']
                )
                # Crear/actualizar perfil extendido con teléfono y hash de DNI
                profile, created = CoreAuthProfile.objects.get_or_create(user=user)
                profile.phone_number = form.cleaned_data.get('phone_number', '')
                dni_last4 = form.cleaned_data.get('dni_last4')
                if dni_last4:
                    profile.dni_last4_hash = make_password(dni_last4)
                profile.recovery_hint = 'Últimos 4 del DNI'
                profile.save()
                
                messages.success(
                    request,
                    _('¡Registro exitoso! Por favor, inicia sesión.')
                )
                return redirect(self.success_url)

            except Exception as e:
                logger.error(f"Error durante el registro: {str(e)}", exc_info=True)
                messages.error(request, 'No se pudo completar el registro')

        # Si hay errores, volver a mostrar el formulario con los errores
        return render(request, self.template_name, {'form': form}, status=200)


class ForgotPasswordInfoView(View):
    template_name = 'core_auth/forgot_password_info.html'

    def get(self, request, *args, **kwargs):
        form = ResetRequestForm()
        ctx = {
            'form': form,
            'whatsapp_contact': getattr(settings, 'WHATSAPP_CONTACT', ''),
            'app_name': getattr(settings, 'NOMBRE_APLICACION', 'Mi Aplicacion'),
        }
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        form = ResetRequestForm(request.POST)
        if not form.is_valid():
            ctx = {
                'form': form,
                'whatsapp_contact': getattr(settings, 'WHATSAPP_CONTACT', ''),
                'app_name': getattr(settings, 'NOMBRE_APLICACION', 'Mi Aplicacion'),
            }
            return render(request, self.template_name, ctx, status=200)

        identifier = form.cleaned_data['identifier'].strip()

        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(username__iexact=identifier).first()
        if not user:
            user = User.objects.filter(email__iexact=identifier).first()

        # Crear ticket mínimo según tests
        PasswordResetRequest.objects.create(
            identifier_submitted=identifier,
            user=user if user else None,
            status='pending',
        )

        # Mostrar la misma página con mensaje
        messages.success(request, _('Tu solicitud fue registrada.'))
        return redirect(reverse('core_auth:forgot_password_info'))


class PasswordChangeEnforcedView(LoginRequiredMixin, View):
    template_name = 'core_auth/password_change_enforced.html'

    def get(self, request, *args, **kwargs):
        form = EnforcedPasswordChangeForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = EnforcedPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Desactivar el flag de forzar cambio
            profile = getattr(user, 'core_profile', None)
            if profile:
                profile.must_change_password = False
                profile.save(update_fields=['must_change_password', 'updated_at'])
            update_session_auth_hash(request, user)
            messages.success(request, _('Tu contraseña fue actualizada correctamente.'))
            return redirect(reverse('core_app:home'))
        return render(request, self.template_name, {'form': form}, status=200)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, _('No tienes permisos para acceder a esta sección.'))
        return redirect('core_auth:login')


class ResetRequestListView(StaffRequiredMixin, View):
    template_name = 'core_auth/staff/reset_requests_list.html'

    def get(self, request, *args, **kwargs):
        # Permitir alternar entre 'accionables' (por defecto) y 'todas' mediante ?scope=all
        scope = (request.GET.get('scope') or '').lower()
        if scope == 'all':
            qs = PasswordResetRequest.objects.select_related('user__core_profile').order_by('-created_at')
        else:
            # Mostrar sólo solicitudes accionables:
            # - pending
            # - approved y el usuario aún debe cambiar la contraseña
            from django.db.models import Q
            qs = PasswordResetRequest.objects.select_related('user__core_profile').filter(
                Q(status='pending') | Q(status='approved', user__core_profile__must_change_password=True)
            ).order_by('-created_at')
        status_filter = request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return render(request, self.template_name, {'requests': qs, 'scope': scope})


class ResetRequestDetailView(StaffRequiredMixin, View):
    template_name = 'core_auth/staff/reset_request_detail.html'

    def get(self, request, pk, *args, **kwargs):
        prr = get_object_or_404(PasswordResetRequest, pk=pk)
        return render(request, self.template_name, {'req': prr})


def _generate_temp_password(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def approve_reset_request(request, pk):
    from django.contrib.admin.views.decorators import staff_member_required

    @staff_member_required
    def _inner(req, pk):
        prr = get_object_or_404(PasswordResetRequest, pk=pk)
        if prr.status not in ('pending', 'under_review', 'ready_to_deliver'):
            messages.error(req, _('La solicitud ya fue procesada.'))
            return redirect(reverse('core_auth:staff_reset_request_detail', args=[pk]))

        # Generar contraseña temporal y aplicar inmediatamente según expectativas de tests
        temp_password = _generate_temp_password(getattr(settings, 'TEMP_PASSWORD_LENGTH', 16))
        prr.temp_password_preview = temp_password
        prr.status = 'processed'
        prr.processed_by = req.user
        prr.processed_at = timezone.now()
        prr.save(update_fields=['temp_password_preview', 'status', 'processed_by', 'processed_at'])

        if prr.user:
            # Aplicar la contraseña y forzar cambio en próximo login
            prr.user.set_password(temp_password)
            prr.user.save()
            profile, created = CoreAuthProfile.objects.get_or_create(user=prr.user)
            profile.must_change_password = True
            profile.save(update_fields=['must_change_password', 'updated_at'])

        messages.success(req, _('Temporal generada y aplicada al usuario.'))
        return redirect(reverse('core_auth:staff_reset_request_detail', args=[pk]))

    return _inner(request, pk)


def deliver_reset_request(request, pk):
    from django.contrib.admin.views.decorators import staff_member_required

    @staff_member_required
    def _inner(req, pk):
        prr = get_object_or_404(PasswordResetRequest, pk=pk)
        if prr.status != 'ready_to_deliver':
            messages.error(req, _('La solicitud no está lista para entregar.'))
            return redirect(reverse('core_auth:staff_reset_request_detail', args=[pk]))

        if not prr.user:
            messages.error(req, _('No se pudo asociar un usuario a esta solicitud.'))
            return redirect(reverse('core_auth:staff_reset_request_detail', args=[pk]))

        if not prr.temp_password_preview:
            messages.error(req, _('No hay contraseña temporal generada.'))
            return redirect(reverse('core_auth:staff_reset_request_detail', args=[pk]))

        # Aplicar la contraseña temporal en el momento de la entrega
        prr.user.set_password(prr.temp_password_preview)
        prr.user.save()

        # Forzar cambio de contraseña al primer login
        profile, created = CoreAuthProfile.objects.get_or_create(user=prr.user)
        profile.must_change_password = True
        profile.save(update_fields=['must_change_password', 'updated_at'])

        prr.status = 'resolved'
        prr.delivered_at = timezone.now()
        prr.save(update_fields=['status', 'delivered_at'])

        messages.success(req, _('Contraseña temporal activada y lista para ser comunicada al usuario.'))
        return redirect(reverse('core_auth:staff_reset_request_detail', args=[pk]))

    return _inner(request, pk)


class LoginView(View):
    """
    Vista para el inicio de sesión de usuarios.
    """
    template_name = 'core_auth/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('core_app:home')
    
    def get(self, request, *args, **kwargs):
        """Muestra el formulario de inicio de sesión."""
        if request.user.is_authenticated:
            return redirect(self.success_url)
            
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        """Procesa el formulario de inicio de sesión."""
        if request.user.is_authenticated:
            return redirect(self.success_url)
            
        form = self.form_class(request, data=request.POST)
        
        # Si no es válido y faltan campos requeridos, devolver formulario con errores
        if not form.is_valid():
            missing_field_errors = ('username' in form.errors) or ('password' in form.errors)
            if missing_field_errors:
                return render(request, self.template_name, {'form': form}, status=200)
            
        try:
            # Ejecutar el caso de uso de autenticación
            use_case = LoginUserUseCase(auth_repository)
            print("\n" + "="*80)
            print("=== LOGIN VIEW: BEFORE USE CASE EXECUTE ===")
            print(f"[INFO] Username/Email: {form.cleaned_data['username']}")
            print(f"[INFO] Password: {'*' * 8}")
            print(f"[INFO] Remember me: {form.cleaned_data.get('remember_me', False)}")
            
            try:
                print("\n[INFO] Calling use_case.execute()...")
                user, remember_me = use_case.execute(
                    username_or_email=form.cleaned_data['username'],
                    password=form.cleaned_data['password'],
                    remember_me=form.cleaned_data.get('remember_me', False)
                )
                
                print("\n[SUCCESS] use_case.execute() completed successfully")
                print(f"[INFO] User: {user}")
                print(f"[INFO] User is_active: {getattr(user, 'is_active', 'N/A')}")
                print(f"[INFO] Remember me: {remember_me}")
            except ValidationError as ve:
                # Map codes to expected messages
                code = getattr(ve, 'code', None)
                def send_error(msg):
                    if hasattr(request, '_messages') and hasattr(request._messages, 'error'):
                        request._messages.error(request, msg)
                    else:
                        messages.error(request, msg)

                if code == 'invalid_credentials':
                    send_error(_("Credenciales inválidas"))
                elif code in ('inactive', 'inactive_user'):
                    send_error(_("Tu cuenta está inactiva."))
                else:
                    # If message provided, use it; otherwise generic
                    msg = ve.messages[0] if getattr(ve, 'messages', None) else _("Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde.")
                    send_error(msg)
                return render(request, self.template_name, {'form': form}, status=200)

            login(request, user)
            
            remember_me = form.cleaned_data.get('remember_me', False)
            if not remember_me:
                request.session.set_expiry(0)

            messages.success(request, _("¡Inicio de sesión exitoso!"))
            return redirect(self.success_url)

        except Exception as e:
            logger.error(f"Error inesperado durante el inicio de sesión: {str(e)}", exc_info=True)
            if hasattr(request, '_messages') and hasattr(request._messages, 'error'):
                request._messages.error(request, _("Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde."))
            else:
                messages.error(request, _("Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde."))
            
        return render(request, self.template_name, {'form': form}, status=200)


class LogoutView(View):
    """
    Vista para cerrar la sesión del usuario.
    """
    success_url = reverse_lazy('core_auth:login')
    
    def get(self, request, *args, **kwargs):
        """Cierra la sesión del usuario."""
        if request.user.is_authenticated:
            try:
                # Ejecutar el caso de uso de cierre de sesión
                use_case = LogoutUserUseCase(auth_repository)
                use_case.execute(request)
                
                messages.success(
                    request,
                    _('Has cerrado sesión exitosamente.')
                )
            except Exception as e:
                print(e)
                messages.error(
                    request,
                    _('Ocurrió un error al cerrar la sesión.')
                )
        
        return redirect(self.success_url)