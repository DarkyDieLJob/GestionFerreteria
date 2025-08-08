import logging
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import login, logout
from django.core.exceptions import ValidationError

# Set up logging
logger = logging.getLogger(__name__)

from .forms import RegisterForm, LoginForm
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