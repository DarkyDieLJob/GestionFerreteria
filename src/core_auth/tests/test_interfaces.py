"""
Pruebas para las interfaces del módulo de autenticación.
Estas pruebas verifican que las interfaces definen correctamente los métodos requeridos.
"""

import pytest
from unittest.mock import Mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import HttpRequest

from core_auth.ports.interfaces import Core_authRepository, AuthRepository

User = get_user_model()


class TestCoreAuthRepositoryInterface(TestCase):
    """Pruebas para la interfaz Core_authRepository."""

    def test_core_auth_repository_interface_methods(self):
        """Verifica que la implementación concreta funcione correctamente."""

        # Crear una implementación concreta de la interfaz
        class ConcreteCoreAuthRepository(Core_authRepository):
            def __init__(self):
                self.data = []

            def save(self, data):
                """Guarda un ítem y devuelve el ítem guardado."""
                if not data:
                    raise ValueError("No se pueden guardar datos vacíos")
                self.data.append(data)
                return data

            def get_all(self):
                """Devuelve todos los ítems guardados."""
                return self.data.copy()

        # Probar la implementación
        repo = ConcreteCoreAuthRepository()

        # Probar save con datos válidos
        test_data = {"id": 1, "name": "Test Item"}
        saved_item = repo.save(test_data)
        assert saved_item == test_data

        # Verificar que se guardó correctamente
        assert len(repo.get_all()) == 1
        assert repo.get_all()[0] == test_data

        # Probar get_all con múltiples ítems
        test_data_2 = {"id": 2, "name": "Another Item"}
        repo.save(test_data_2)
        assert len(repo.get_all()) == 2

        # Probar save con datos inválidos
        with pytest.raises(ValueError):
            repo.save(None)

    def test_core_auth_repository_interface_contract(self):
        """Verifica que la interfaz Core_authRepository defina los métodos requeridos."""

        # Crear una implementación concreta de la interfaz
        class ConcreteCoreAuthRepository(Core_authRepository):
            def save(self, data):
                """Método save de ejemplo."""
                return f"saved: {data}"

            def get_all(self):
                """Método get_all de ejemplo."""
                return ["item1", "item2"]

        # Verificar que se puede instanciar y usar la implementación
        repo = ConcreteCoreAuthRepository()
        assert repo.save("test") == "saved: test"
        assert repo.get_all() == ["item1", "item2"]

    def test_core_auth_repository_abstract_methods_enforcement(self):
        """Verifica que no se pueda instanciar la clase base abstracta."""
        with pytest.raises(TypeError) as excinfo:
            Core_authRepository()

        # Verificar que el mensaje de error menciona los métodos abstractos
        error_msg = str(excinfo.value).lower()
        assert "abstract" in error_msg
        assert "save" in error_msg
        assert "get_all" in error_msg


class TestAuthRepositoryInterface(TestCase):
    """Pruebas para la interfaz AuthRepository."""

    def test_auth_repository_interface_contract(self):
        """Verifica que la implementación concreta cumpla con el contrato de la interfaz."""

        # Crear una implementación concreta de la interfaz
        class ConcreteAuthRepository(AuthRepository):
            def __init__(self):
                self.users = {}
                self.sessions = set()

            def create_user(self, username, email, password):
                """Crea un nuevo usuario en el sistema."""
                if username in self.users:
                    raise ValueError(f"El usuario {username} ya existe")
                if any(u.email == email for u in self.users.values()):
                    raise ValueError(f"El email {email} ya está registrado")

                user = Mock(
                    spec=User,
                    username=username,
                    email=email,
                    is_active=True,
                    check_password=lambda p: p == password,
                )
                self.users[username] = user
                return user

            def authenticate_user(self, username_or_email, password):
                """Autentica un usuario con nombre de usuario/email y contraseña."""
                # Buscar por nombre de usuario
                user = self.users.get(username_or_email)

                # Si no se encuentra por nombre de usuario, buscar por email
                if user is None and "@" in username_or_email:
                    user = next(
                        (
                            u
                            for u in self.users.values()
                            if getattr(u, "email", None) == username_or_email
                        ),
                        None,
                    )

                if user and user.check_password(password) and user.is_active:
                    return user
                return None

            def logout_user(self, request):
                """Cierra la sesión del usuario actual."""
                if hasattr(request, "session") and hasattr(request.session, "flush"):
                    request.session.flush()
                self.sessions.discard(id(request))

        # Probar la implementación
        repo = ConcreteAuthRepository()

        # Probar create_user exitoso
        user = repo.create_user("testuser", "test@example.com", "password123")
        assert user.username == "testuser"
        assert user.email == "test@example.com"

        # Probar que no se pueden crear usuarios duplicados
        with pytest.raises(ValueError):
            repo.create_user("testuser", "another@example.com", "pass")

        # Probar que no se pueden crear emails duplicados
        with pytest.raises(ValueError):
            repo.create_user("anotheruser", "test@example.com", "pass")

        # Probar autenticación exitosa por nombre de usuario
        auth_user = repo.authenticate_user("testuser", "password123")
        assert auth_user is not None
        assert auth_user.username == "testuser"

        # Probar autenticación exitosa por email
        auth_user = repo.authenticate_user("test@example.com", "password123")
        assert auth_user is not None

        # Probar autenticación con credenciales inválidas
        assert repo.authenticate_user("testuser", "wrongpass") is None
        assert repo.authenticate_user("nonexistent", "pass") is None

        # Probar logout
        request = HttpRequest()
        mock_session = Mock()
        mock_session.flush = Mock()
        request.session = mock_session

        repo.logout_user(request)
        mock_session.flush.assert_called_once()
        assert id(request) not in repo.sessions

    def test_auth_repository_interface_abstract_methods_enforcement(self):
        """Verifica que no se pueda instanciar la clase base abstracta."""
        with pytest.raises(TypeError) as excinfo:
            AuthRepository()

        # Verificar que el mensaje de error menciona los métodos abstractos
        error_msg = str(excinfo.value).lower()
        assert "abstract" in error_msg
        assert "create_user" in error_msg
        assert "authenticate_user" in error_msg
        assert "logout_user" in error_msg
