"""
Pruebas unitarias para los casos de uso del módulo de autenticación.
"""

from unittest.mock import Mock, patch
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from core_auth.domain.use_cases import (
    RegisterUserUseCase,
    LoginUserUseCase,
    LogoutUserUseCase,
)

User = get_user_model()


class TestRegisterUserUseCase(TestCase):
    """Pruebas para el caso de uso RegisterUserUseCase."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.mock_repository = Mock()
        self.use_case = RegisterUserUseCase(self.mock_repository)

        # Datos de prueba
        self.valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        }

    def test_register_user_success(self):
        """Prueba el registro exitoso de un usuario."""
        # Configurar el mock para simular un registro exitoso
        mock_user = Mock()
        self.mock_repository.create_user.return_value = mock_user

        # Ejecutar el caso de uso
        result = self.use_case.execute(
            username=self.valid_data["username"],
            email=self.valid_data["email"],
            password=self.valid_data["password"],
        )

        # Verificar que se llamó al repositorio con los datos correctos
        self.mock_repository.create_user.assert_called_once_with(
            username=self.valid_data["username"],
            email=self.valid_data["email"],
            password=self.valid_data["password"],
        )

        # Verificar que se devolvió el usuario creado
        self.assertEqual(result, mock_user)

    def test_register_user_missing_fields(self):
        """Prueba que se lance una excepción cuando faltan campos obligatorios."""
        with self.assertRaises(ValidationError) as context:
            self.use_case.execute(username="", email="", password="")

        self.assertIn("obligatorios", str(context.exception))

    def test_register_user_short_password(self):
        """Prueba que se valide la longitud mínima de la contraseña."""
        with self.assertRaises(ValidationError) as context:
            self.use_case.execute(
                username="testuser", email="test@example.com", password="short"
            )

        self.assertIn("8 caracteres", str(context.exception))

    def test_register_user_duplicate_username(self):
        """Prueba el manejo de nombres de usuario duplicados."""
        self.mock_repository.create_user.side_effect = Exception(
            "User with this username already exists"
        )

        with self.assertRaises(ValidationError) as context:
            self.use_case.execute(**self.valid_data)

        self.assertIn("nombre de usuario ya está en uso", str(context.exception))

    def test_register_user_duplicate_email(self):
        """Prueba el manejo de correos electrónicos duplicados."""
        self.mock_repository.create_user.side_effect = Exception(
            "User with this email already exists"
        )

        with self.assertRaises(ValidationError) as context:
            self.use_case.execute(**self.valid_data)

        self.assertIn("correo electrónico ya está registrado", str(context.exception))

    def test_register_user_generic_exception(self):
        """Prueba el manejo de excepciones genéricas durante el registro."""
        # Configurar el mock para lanzar una excepción genérica
        self.mock_repository.create_user.side_effect = Exception(
            "Database connection error"
        )

        with self.assertRaises(ValidationError) as context:
            self.use_case.execute(**self.valid_data)

        # Verificar que el mensaje de error genérico se muestra
        self.assertIn("No se pudo crear el usuario", str(context.exception))
        self.assertIn("Database connection error", str(context.exception))


class TestLoginUserUseCase(TestCase):
    """Pruebas para el caso de uso LoginUserUseCase."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.mock_repository = Mock()
        self.use_case = LoginUserUseCase(self.mock_repository)

        # Datos de prueba
        self.valid_credentials = {
            "username_or_email": "testuser",
            "password": "testpass123",
            "remember_me": False,
        }

        # Usuario de prueba
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_login_success_with_username(self):
        """Prueba el inicio de sesión exitoso con nombre de usuario."""
        # Configurar el mock para simular autenticación exitosa
        self.mock_repository.authenticate_user.return_value = self.test_user

        # Ejecutar el caso de uso
        result = self.use_case.execute(
            username_or_email=self.valid_credentials["username_or_email"],
            password=self.valid_credentials["password"],
            remember_me=self.valid_credentials["remember_me"],
        )

        # Verificar que se llamó al repositorio con los datos correctos
        self.mock_repository.authenticate_user.assert_called_once_with(
            self.valid_credentials["username_or_email"],
            self.valid_credentials["password"],
        )

        # Verificar que se devolvió el usuario autenticado y el flag remember_me
        self.assertEqual(result, (self.test_user, False))

    def test_login_success_with_email(self):
        """Prueba el inicio de sesión exitoso con correo electrónico."""
        # Configurar el mock para simular autenticación exitosa
        self.mock_repository.authenticate_user.return_value = self.test_user

        # Ejecutar el caso de uso con email
        self.use_case.execute(
            username_or_email="test@example.com",
            password=self.valid_credentials["password"],
            remember_me=self.valid_credentials["remember_me"],
        )

        # Verificar que se llamó al repositorio con el email
        self.mock_repository.authenticate_user.assert_called_once_with(
            "test@example.com", self.valid_credentials["password"]
        )

    def test_login_remember_me(self):
        """Prueba que se configure correctamente 'recordarme'."""
        self.mock_repository.authenticate_user.return_value = self.test_user

        # Ejecutar con remember_me=True
        self.use_case.execute(
            username_or_email=self.valid_credentials["username_or_email"],
            password=self.valid_credentials["password"],
            remember_me=True,
        )

        # Verificar que no se configuró la expiración de la sesión
        self.mock_repository.set_session_expiry.assert_not_called()

    def test_login_invalid_credentials(self):
        """Prueba el manejo de credenciales inválidas."""
        self.mock_repository.authenticate_user.return_value = None

        with self.assertRaises(ValidationError) as context:
            self.use_case.execute(
                username_or_email="nonexistent",
                password="wrongpassword",
                remember_me=False,
            )

        self.assertEqual(context.exception.messages[0], "Credenciales inválidas")

    def test_login_inactive_user(self):
        """Prueba el manejo de cuentas inactivas."""
        # Crear un usuario inactivo
        inactive_user = User.objects.create_user(
            username="inactive",
            email="inactive@example.com",
            password="testpass123",
            is_active=False,
        )

        self.mock_repository.authenticate_user.return_value = inactive_user

        with self.assertRaises(ValidationError) as context:
            self.use_case.execute(
                username_or_email="inactive", password="testpass123", remember_me=False
            )

        self.assertEqual(context.exception.messages[0], "Tu cuenta está inactiva.")

    def test_login_auth_service_error(self):
        """Prueba el manejo de errores en el servicio de autenticación."""
        # Configurar el mock para lanzar una excepción
        self.mock_repository.authenticate_user.side_effect = Exception(
            "Authentication service unavailable"
        )

        with self.assertRaises(ValidationError) as context:
            self.use_case.execute(
                username_or_email="testuser", password="testpass123", remember_me=False
            )

        # Verificar que se muestra un mensaje de error genérico
        self.assertIn("Error al intentar autenticar", str(context.exception))


class TestLogoutUserUseCase(TestCase):
    """Pruebas para el caso de uso LogoutUserUseCase."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.mock_repository = Mock()
        self.use_case = LogoutUserUseCase(self.mock_repository)

        # Crear una solicitud simulada
        self.request = Mock()

    def test_logout_success(self):
        """Prueba el cierre de sesión exitoso."""
        # Ejecutar el caso de uso
        self.use_case.execute(self.request)

        # Verificar que se llamó al método de logout del repositorio
        self.mock_repository.logout_user.assert_called_once_with(self.request)

    def test_logout_exception_handling(self):
        """Prueba el manejo de excepciones durante el cierre de sesión."""
        # Configurar el mock para lanzar una excepción
        self.mock_repository.logout_user.side_effect = Exception("Logout error")

        # Verificar que la excepción se propaga
        with self.assertRaises(Exception) as context:
            self.use_case.execute(self.request)

        # Verificar que se llamó al método de logout del repositorio
        self.mock_repository.logout_user.assert_called_once_with(self.request)
        # Verificar que la excepción original se propaga
        self.assertEqual(str(context.exception), "Logout error")
