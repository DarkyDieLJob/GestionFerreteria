from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión personalizado."""
    username = forms.CharField(
        label=_("Usuario o Correo"),
        widget=forms.TextInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Usuario o Correo',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Contraseña',
        }),
    )
    remember_me = forms.BooleanField(
        required=False,
        label=_("Recordar sesión"),
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded',
        })
    )

    error_messages = {
        'invalid_login': _("Credenciales inválidas"),
        'inactive': _("Esta cuenta está inactiva"),
    }


class RegisterForm(UserCreationForm):
    """Formulario de registro de usuario personalizado."""
    phone_number = forms.CharField(
        label=_("Teléfono (opcional)"),
        required=False,
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Teléfono (opcional)'
        })
    )
    dni_last4 = forms.CharField(
        label=_("Últimos 4 del DNI"),
        required=False,
        max_length=4,
        min_length=4,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Ej: 1234',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'autocomplete': 'off',
        })
    )
    email = forms.EmailField(
        label=_("Correo electrónico"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Correo electrónico',
            'autocomplete': 'email',
        })
    )
    username = forms.CharField(
        label=_("Nombre de usuario"),
        max_length=150,
        help_text=_("Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente."),
        widget=forms.TextInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Nombre de usuario',
            'autocomplete': 'username',
        })
    )
    password1 = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        help_text=_("Tu contraseña debe contener al menos 8 caracteres y no puede ser una contraseña común."),
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Contraseña',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        label=_("Confirmar contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Confirmar contraseña',
            'autocomplete': 'new-password',
        }),
    )
    terms = forms.BooleanField(
        required=True,
        label=_("Acepto los términos y condiciones"),
        error_messages={
            'required': _("Debes aceptar los términos y condiciones para registrarte.")
        },
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Ya existe un usuario con este correo electrónico."))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(_("Este nombre de usuario ya está en uso."))
        return username

    def clean_dni_last4(self):
        value = (self.cleaned_data.get('dni_last4') or '').strip()
        # Permitir vacío (el campo es opcional). Si se proporciona, validar 4 dígitos.
        if not value:
            return ''
        if not (len(value) == 4 and value.isdigit()):
            raise ValidationError(_("Debes ingresar exactamente 4 dígitos."))
        return value


class ResetRequestForm(forms.Form):
    """Formulario público simplificado: acepta un único identificador (usuario o email)."""
    identifier = forms.CharField(
        label=_('Usuario o Email'), required=True, max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Tu usuario o email',
            'autocomplete': 'username',
        })
    )
