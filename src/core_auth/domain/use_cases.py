from typing import Optional
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RegisterUserUseCase:
    """
    Caso de uso para el registro de nuevos usuarios.
    Maneja la lógica de negocio relacionada con la creación de cuentas de usuario.
    """

    def __init__(self, auth_repository):
        """
        Inicializa el caso de uso con un repositorio de autenticación.

        Args:
            auth_repository: Repositorio que implementa la interfaz AuthRepository
        """
        self.auth_repository = auth_repository

    def execute(self, username: str, email: str, password: str) -> User:
        """
        Ejecuta el caso de uso de registro de usuario.

        Args:
            username: Nombre de usuario único
            email: Correo electrónico del usuario
            password: Contraseña en texto plano

        Returns:
            User: Instancia del usuario creado

        Raises:
            ValueError: Si el usuario no puede ser creado (ej: usuario/email ya existe)
            ValidationError: Si los datos no cumplen con las validaciones
        """
        # Validaciones adicionales de negocio
        if not username or not email or not password:
            raise ValidationError(_("Todos los campos son obligatorios"))

        if len(password) < 8:
            raise ValidationError(_("La contraseña debe tener al menos 8 caracteres"))

        # Delegar la creación del usuario al repositorio
        try:
            user = self.auth_repository.create_user(
                username=username, email=email, password=password
            )
            return user

        except Exception as e:
            # Mejorar el mensaje de error para el usuario final
            if "username" in str(e).lower() and "already exists" in str(e).lower():
                raise ValidationError(_("El nombre de usuario ya está en uso"))
            elif "email" in str(e).lower() and "already exists" in str(e).lower():
                raise ValidationError(_("El correo electrónico ya está registrado"))
            raise ValidationError(
                _("No se pudo crear el usuario: %(error)s") % {"error": str(e)}
            )


class LoginUserUseCase:
    """
    Caso de uso para la autenticación de usuarios.
    Maneja la lógica de negocio relacionada con el inicio de sesión.
    """

    def __init__(self, auth_repository):
        """
        Inicializa el caso de uso con un repositorio de autenticación.

        Args:
            auth_repository: Repositorio que implementa la interfaz AuthRepository
        """
        self.auth_repository = auth_repository

    def execute(
        self, username_or_email: str, password: str, remember_me: bool = False
    ) -> User:
        """
        Ejecuta el caso de uso de autenticación de usuario.

        Args:
            username_or_email: Nombre de usuario o correo electrónico
            password: Contraseña en texto plano
            remember_me: Si es True, la sesión será persistente

        Returns:
            User: Instancia del usuario autenticado

        Raises:
            ValidationError: Si las credenciales son inválidas o la cuenta está inactiva
        """
        print("\n" + "=" * 80)
        print("=== LOGIN USER USE CASE EXECUTE ===")
        print(f"Username/Email: {username_or_email}")
        print(f"Password provided: {'*' * len(password) if password else 'None'}")
        print(f"Remember me: {remember_me}")

        # Validar que se hayan proporcionado credenciales
        if not username_or_email or not password:
            print("\n[ERROR] Validation failed: Missing username/email or password")
            error = ValidationError(
                _("Por favor ingresa tus credenciales"), code="missing_credentials"
            )
            print(f"[ERROR] Raising ValidationError: {error}")
            print(f"[ERROR] Error code: {getattr(error, 'code', 'No code')}")
            print(
                f"[ERROR] Error messages: {getattr(error, 'messages', 'No messages')}"
            )
            raise error

        try:
            # Intentar autenticar al usuario a través del repositorio
            print("\n[INFO] Attempting to authenticate user...")
            user = self.auth_repository.authenticate_user(username_or_email, password)
            print(f"[INFO] Auth repository returned user: {user}")

            if user is None:
                # No revelar si el usuario no existe o la contraseña es incorrecta
                print("\n[ERROR] Authentication failed: Invalid credentials")
                error = ValidationError(
                    _("Credenciales inválidas"), code="invalid_credentials"
                )
                print(f"[ERROR] Raising ValidationError: {error}")
                print(f"[ERROR] Error code: {getattr(error, 'code', 'No code')}")
                print(
                    f"[ERROR] Error messages: {getattr(error, 'messages', 'No messages')}"
                )
                raise error

            print(f"\n[INFO] User is_active status: {user.is_active}")
            if not user.is_active:
                print("\n[ERROR] Authentication failed: User account is inactive")
                # Usar el código y mensaje exactos esperados por las pruebas
                error_msg = _("Tu cuenta está inactiva.")
                error = ValidationError(error_msg, code="inactive_user")
                print(f"[ERROR] Raising ValidationError: {error}")
                print(f"[ERROR] Error code: {getattr(error, 'code', 'No code')}")
                print(
                    f"[ERROR] Error messages: {getattr(error, 'messages', 'No messages')}"
                )
                print(
                    f"[ERROR] Error message_dict: {getattr(error, 'message_dict', 'No message_dict')}"
                )
                raise error

            print("\n[SUCCESS] Authentication successful")
            # Devolver también el valor de remember_me para que la vista pueda manejar la sesión
            return user, remember_me

        except ValidationError as ve:
            print("\n[EXCEPTION] Caught ValidationError in use case")
            print(f"[EXCEPTION] Error: {ve}")
            print(f"[EXCEPTION] Error code: {getattr(ve, 'code', 'No code')}")
            print(
                f"[EXCEPTION] Error messages: {getattr(ve, 'messages', 'No messages')}"
            )
            print(
                f"[EXCEPTION] Error message_dict: {getattr(ve, 'message_dict', 'No message_dict')}"
            )

            # No mutar internamente ValidationError (atributos como message_dict son solo-lectura).
            # Re-lanzar una nueva ValidationError preservando mensajes y código cuando sea posible.
            messages = getattr(ve, "messages", None) or [str(ve)]
            code = getattr(ve, "code", None) or "validation_error"
            print("\n[EXCEPTION] Re-raising sanitized ValidationError")
            print(f"[EXCEPTION] Sanitized code: {code}")
            print(f"[EXCEPTION] Sanitized messages: {messages}")
            print("=" * 80 + "\n")
            raise ValidationError(messages, code=code)

        except Exception as e:
            # Log the actual error for debugging purposes
            print("\n[ERROR] Unexpected error during authentication:")
            print(f"[ERROR] {str(e)}")
            import traceback

            traceback.print_exc()
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error inesperado durante la autenticación: {str(e)}")

            # Envolver en ValidationError con un código de error genérico
            error = ValidationError(
                _("Error al intentar autenticar"), code="authentication_error"
            )
            print("\n[ERROR] Raising ValidationError:")
            print(f"[ERROR] {error}")
            print(f"[ERROR] Error code: {getattr(error, 'code', 'No code')}")
            print(
                f"[ERROR] Error messages: {getattr(error, 'messages', 'No messages')}"
            )
            print("=" * 80 + "\n")
            raise error


class LogoutUserUseCase:
    """
    Caso de uso para cerrar la sesión de un usuario.
    Maneja la lógica de negocio relacionada con el cierre de sesión.
    """

    def __init__(self, auth_repository):
        """
        Inicializa el caso de uso con un repositorio de autenticación.

        Args:
            auth_repository: Repositorio que implementa la interfaz AuthRepository
        """
        self.auth_repository = auth_repository

    def execute(self, request: HttpRequest) -> None:
        """
        Ejecuta el caso de uso de cierre de sesión.

        Args:
            request: Objeto HttpRequest de Django
        """
        # Limpiar la sesión actual
        self.auth_repository.logout_user(request)
