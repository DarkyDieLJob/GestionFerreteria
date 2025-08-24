from typing import Optional
from django.contrib.auth import get_user_model, authenticate, logout
from django.db import IntegrityError, DatabaseError
from django.http import HttpRequest

from ..ports.interfaces import AuthRepository

User = get_user_model()


class DjangoAuthRepository(AuthRepository):
    """
    Implementación concreta del repositorio de autenticación usando Django.
    Proporciona funcionalidad para crear usuarios, autenticarlos y cerrar sesión.
    """

    def create_user(self, username: str, email: str, password: str) -> User:
        """
        Crea un nuevo usuario en el sistema.

        Args:
            username: Nombre de usuario único
            email: Correo electrónico del usuario
            password: Contraseña en texto plano

        Returns:
            User: Instancia del usuario creado

        Raises:
            ValueError: Si el usuario no puede ser creado (usuario/email ya existe)
            DatabaseError: Si ocurre un error en la base de datos
        """
        try:
            return User.objects.create_user(
                username=username, email=email, password=password
            )
        except IntegrityError as e:
            if "username" in str(e).lower():
                raise ValueError(f"El nombre de usuario '{username}' ya está en uso.")
            elif "email" in str(e).lower():
                raise ValueError(f"El correo electrónico '{email}' ya está registrado.")
            raise ValueError(
                "Error al crear el usuario. Por favor, intente nuevamente."
            )
        except Exception as e:
            raise DatabaseError(f"Error en la base de datos: {str(e)}")

    def authenticate_user(
        self, username_or_email: str, password: str
    ) -> Optional[User]:
        """
        Autentica un usuario con nombre de usuario/email y contraseña.

        Args:
            username_or_email: Nombre de usuario o correo electrónico
            password: Contraseña en texto plano

        Returns:
            User: Instancia del usuario autenticado si las credenciales son válidas
            None: Si las credenciales son inválidas

        Raises:
            DatabaseError: Si ocurre un error en la base de datos
        """
        try:
            # Primero intentamos autenticar directamente (para nombres de usuario)
            user = authenticate(username=username_or_email, password=password)

            # Si no funciona, intentamos buscar por email
            if user is None and "@" in username_or_email:
                try:
                    user = User.objects.get(email=username_or_email)
                    user = authenticate(username=user.username, password=password)
                except User.DoesNotExist:
                    return None

            return user

        except Exception as e:
            raise DatabaseError(f"Error durante la autenticación: {str(e)}")

    def logout_user(self, request: HttpRequest) -> None:
        """
        Cierra la sesión del usuario actual.

        Args:
            request: Objeto HttpRequest de Django

        Raises:
            Exception: Si ocurre un error durante el cierre de sesión
        """
        try:
            logout(request)
        except Exception as e:
            raise Exception(f"Error al cerrar la sesión: {str(e)}")


# Mantenemos la clase existente para compatibilidad
class DjangoCore_authRepository:
    def save(self, data):
        # Implementación existente
        pass

    def get_all(self):
        # Implementación existente
        pass
