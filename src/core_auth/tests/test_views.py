"""Tests for core_auth views."""
import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.messages import get_messages

User = get_user_model()

class TestLoginView(TestCase):
    """Test the login view."""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('core_auth:login')
        self.home_url = reverse('core_app:home')

    def test_login_view_get(self):
        """Test GET request to login view."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        from core_auth.adapters.forms import LoginForm
        self.assertIsInstance(response.context['form'], LoginForm)

    def test_login_view_get_authenticated(self):
        """Test GET request to login view when already authenticated."""
        User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.login_url, follow=True)
        self.assertRedirects(response, self.home_url)

    def test_login_authenticated_redirect(self):
        """Test that authenticated users are redirected from login page."""
        User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.login_url, follow=True)
        self.assertRedirects(response, self.home_url)

    def test_login_missing_credentials(self):
        """Test login with missing credentials shows form errors."""
        response = self.client.post(self.login_url, {}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('core_auth/login.html')
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('username', form.errors)
        self.assertIn('password', form.errors)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials shows error message."""
        User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        response = self.client.post(self.login_url, {'username': 'testuser', 'password': 'wrongpassword'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core_auth/login.html')
        self.assertIn('Credenciales inválidas', response.content.decode())
        self.assertFalse(response.context['user'].is_authenticated)

    def test_login_successful_username(self):
        """Test successful login with username."""
        User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        response = self.client.post(self.login_url, {'username': 'testuser', 'password': 'testpass123'}, follow=True)
        self.assertRedirects(response, self.home_url)
        self.assertTrue(response.context['user'].is_authenticated)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '¡Inicio de sesión exitoso!')

    def test_login_with_email(self):
        """Test successful login with email."""
        User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        response = self.client.post(self.login_url, {'username': 'test@example.com', 'password': 'testpass123'}, follow=True)
        self.assertRedirects(response, self.home_url)
        self.assertTrue(response.context['user'].is_authenticated)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '¡Inicio de sesión exitoso!')

    @patch('core_auth.adapters.views.LoginUserUseCase')
    def test_login_validation_error(self, MockLoginUseCase):
        """Test login with a validation error from the use case."""
        MockLoginUseCase.return_value.execute.side_effect = ValidationError('Credenciales inválidas', code='invalid_credentials')
        response = self.client.post(self.login_url, {'username': 'testuser', 'password': 'password123'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core_auth/login.html')
        self.assertIn('Credenciales inválidas', response.content.decode())
        self.assertFalse(response.context['user'].is_authenticated)

    @patch('core_auth.adapters.views.LoginUserUseCase')
    def test_login_generic_exception(self, MockLoginUseCase):
        """Test that generic exceptions during login are properly handled."""
        MockLoginUseCase.return_value.execute.side_effect = Exception("Unexpected error")
        response = self.client.post(self.login_url, {'username': 'testuser', 'password': 'password123'})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde.")

    @patch('core_auth.adapters.views.LoginUserUseCase')
    def test_login_inactive_user(self, MockLoginUseCase):
        """Test login with inactive user."""
        MockLoginUseCase.return_value.execute.side_effect = ValidationError('Tu cuenta está inactiva.', code='inactive')
        response = self.client.post(self.login_url, {'username': 'inactiveuser', 'password': 'password123'})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Tu cuenta está inactiva.')

class TestLogoutView(TestCase):
    """Test the logout view."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()
        self.client.login(username='testuser', password='password123')
        self.logout_url = reverse('core_auth:logout')
        self.login_url = reverse('core_auth:login')

    def test_logout_authenticated(self):
        """Test that authenticated users can log out successfully."""
        response = self.client.get(self.logout_url, follow=True)
        self.assertRedirects(response, self.login_url)
        self.assertFalse('_auth_user_id' in self.client.session)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Has cerrado sesión exitosamente.')

    def test_logout_unauthenticated(self):
        """Test logout for unauthenticated user."""
        self.client.logout()
        response = self.client.get(self.logout_url, follow=True)
        self.assertRedirects(response, self.login_url)

    def test_logout_post_request(self):
        """Test that POST requests to logout are not allowed."""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 405)

class TestRegisterView(TestCase):
    """Test the user registration view."""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('core_auth:register')
        self.login_url = reverse('core_auth:login')

    def test_register_view_get(self):
        """Test GET request to register view."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        from core_auth.adapters.forms import RegisterForm
        self.assertIsInstance(response.context['form'], RegisterForm)

    def test_register_successful(self):
        """Test successful user registration."""
        user_data = {'username': 'newuser', 'email': 'new@example.com', 'password': 'testpass123', 'terms': True}
        response = self.client.post(self.register_url, user_data, follow=True)
        self.assertRedirects(response, self.login_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '¡Registro exitoso! Por favor, inicia sesión.')

    def test_register_duplicate_username(self):
        """Test registration with duplicate username."""
        User.objects.create_user(username='existinguser', email='test@example.com', password='password123')
        user_data = {'username': 'existinguser', 'email': 'new@example.com', 'password': 'testpass123', 'terms': True}
        response = self.client.post(self.register_url, user_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)

    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        User.objects.create_user(username='existinguser', email='test@example.com', password='password123')
        user_data = {'username': 'newuser', 'email': 'test@example.com', 'password': 'testpass123', 'terms': True}
        response = self.client.post(self.register_url, user_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)

class TestHomeView(TestCase):
    """Test the home view."""

    def setUp(self):
        self.client = Client()
        self.home_url = reverse('core_app:home')
        self.login_url = reverse('core_auth:login')

    def test_home_authenticated(self):
        """Test home page access for authenticated user."""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core_app/home.html')

    def test_home_unauthenticated(self):
        """Test home page access for unauthenticated user."""
        response = self.client.get(self.home_url, follow=True)
        self.assertRedirects(response, f'{self.login_url}?next={self.home_url}')
