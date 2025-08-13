import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from unittest.mock import patch, MagicMock

from django.core.exceptions import ValidationError
from ..adapters.views import LoginView

User = get_user_model()

@pytest.mark.django_db
class TestLoginViewCoverage:
    def test_get_redirects_if_authenticated(self):
        """Verifica que un usuario autenticado sea redirigido.

        GIVEN un usuario autenticado
        WHEN se realiza una solicitud GET a la página de login
        THEN el usuario es redirigido a la página de inicio.
        """
        user = User.objects.create_user(username='testuser', password='password123')
        factory = RequestFactory()
        request = factory.get(reverse('core_auth:login'))
        request.user = user

        response = LoginView.as_view()(request)

        assert response.status_code == 302
        assert response.url == reverse('core_app:home')

    def test_post_redirects_if_authenticated(self):
        """Verifica que un usuario autenticado sea redirigido en POST.

        GIVEN un usuario autenticado
        WHEN se realiza una solicitud POST a la página de login
        THEN el usuario es redirigido a la página de inicio.
        """
        user = User.objects.create_user(username='testuser', password='password123')
        factory = RequestFactory()
        request = factory.post(reverse('core_auth:login'))
        request.user = user

        response = LoginView.as_view()(request)

        assert response.status_code == 302
        assert response.url == reverse('core_app:home')

    def test_post_invalid_credentials(self):
        """Verifica el manejo de credenciales inválidas.

        GIVEN un usuario no autenticado
        WHEN el caso de uso lanza una excepción de validación
        THEN se muestra un error de credenciales inválidas.
        """
        factory = RequestFactory()
        data = {'username': 'testuser', 'password': 'wrongpassword'}
        request = factory.post(reverse('core_auth:login'), data)
        request.user = MagicMock(is_authenticated=False)
        setattr(request, 'session', 'session')
        messages = MagicMock()
        setattr(request, '_messages', messages)

        with patch('core_auth.adapters.views.LoginUserUseCase') as MockLoginUseCase:
            mock_use_case_instance = MockLoginUseCase.return_value
            mock_use_case_instance.execute.side_effect = ValidationError(
                'Credenciales inválidas', code='invalid_credentials'
            )

            response = LoginView.as_view()(request)

            assert response.status_code == 200
            messages.error.assert_called_with(request, 'Credenciales inválidas')

    def test_post_inactive_user(self):
        """Verifica el manejo de un usuario inactivo.

        GIVEN un usuario inactivo
        WHEN se intenta iniciar sesión con sus credenciales
        THEN se muestra un error de cuenta inactiva.
        """
        factory = RequestFactory()
        data = {'username': 'inactiveuser', 'password': 'password123'}
        request = factory.post(reverse('core_auth:login'), data)
        request.user = MagicMock(is_authenticated=False)
        setattr(request, 'session', 'session')
        messages = MagicMock()
        setattr(request, '_messages', messages)

        with patch('core_auth.adapters.views.LoginUserUseCase') as MockLoginUseCase:
            mock_use_case_instance = MockLoginUseCase.return_value
            mock_use_case_instance.execute.side_effect = ValidationError(
                'Tu cuenta está inactiva.', code='inactive'
            )

            response = LoginView.as_view()(request)

            assert response.status_code == 200
            messages.error.assert_called_with(request, 'Tu cuenta está inactiva.')

    def test_post_generic_exception(self):
        """Verifica el manejo de una excepción genérica.

        GIVEN un error inesperado durante el inicio de sesión
        WHEN se intenta iniciar sesión
        THEN se muestra un mensaje de error genérico.
        """
        factory = RequestFactory()
        data = {'username': 'testuser', 'password': 'password123'}
        request = factory.post(reverse('core_auth:login'), data)
        request.user = MagicMock(is_authenticated=False)
        setattr(request, 'session', 'session')
        messages = MagicMock()
        setattr(request, '_messages', messages)

        with patch('core_auth.adapters.views.LoginUserUseCase') as MockLoginUseCase:
            mock_use_case_instance = MockLoginUseCase.return_value
            mock_use_case_instance.execute.side_effect = Exception('Error inesperado')

            response = LoginView.as_view()(request)

            assert response.status_code == 200
            messages.error.assert_called_with(request, 'Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde.')
