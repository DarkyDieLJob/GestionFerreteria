"""
Pruebas para los adaptadores de autenticación.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..adapters.repository import DjangoAuthRepository

User = get_user_model()


class DjangoAuthRepositoryTests(TestCase):
    """Pruebas para el adaptador DjangoAuthRepository."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.repository = DjangoAuthRepository()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.factory = RequestFactory()
    
    def test_create_user_success(self):
        """Prueba la creación exitosa de un usuario."""
        user = self.repository.create_user(
            self.user_data['username'],
            self.user_data['email'],
            self.user_data['password']
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.username, self.user_data['username'])
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
    
    def test_create_user_duplicate_username(self):
        """Prueba la creación de usuario con nombre de usuario duplicado."""
        # Crear usuario inicial
        User.objects.create_user(
            username=self.user_data['username'],
            email='other@example.com',
            password='otherpass'
        )
        
        # Intentar crear usuario con mismo username
        with self.assertRaises(ValueError) as context:
            self.repository.create_user(
                self.user_data['username'],
                'new@example.com',
                'newpass123'
            )
        
        self.assertIn('ya está en uso', str(context.exception))
    
    @patch('django.contrib.auth.get_user_model')
    def test_create_user_duplicate_email(self, mock_user_model):
        """Prueba la creación de usuario con correo electrónico duplicado."""
        # Configurar el mock para simular un error de integridad de email
        mock_user_model.return_value = User
        with patch.object(User.objects, 'create_user') as mock_create:
            # Simular un error de integridad para email duplicado
            from django.db import IntegrityError
            import sqlite3
            mock_create.side_effect = IntegrityError("UNIQUE constraint failed: auth_user.email")
            
            # Intentar crear usuario con email duplicado
            with self.assertRaises(ValueError) as context:
                self.repository.create_user(
                    'newuser',
                    self.user_data['email'],
                    'newpass123'
                )
            
            self.assertIn('ya está registrado', str(context.exception))
    
    def test_authenticate_user_success_username(self):
        """Prueba la autenticación exitosa con nombre de usuario."""
        # Crear usuario de prueba
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        
        # Autenticar con nombre de usuario
        authenticated_user = self.repository.authenticate_user(
            self.user_data['username'],
            self.user_data['password']
        )
        
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user, user)
    
    def test_authenticate_user_success_email(self):
        """Prueba la autenticación exitosa con correo electrónico."""
        # Crear usuario de prueba
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        
        # Autenticar con correo electrónico
        authenticated_user = self.repository.authenticate_user(
            self.user_data['email'],
            self.user_data['password']
        )
        
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user, user)
    
    def test_authenticate_user_invalid_credentials(self):
        """Prueba la autenticación con credenciales inválidas."""
        # Crear usuario de prueba
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        
        # Intentar autenticar con contraseña incorrecta
        authenticated_user = self.repository.authenticate_user(
            self.user_data['username'],
            'wrongpassword'
        )
        
        self.assertIsNone(authenticated_user)
    
    @patch('core_auth.adapters.repository.logout')
    def test_logout_user(self, mock_logout):
        """Prueba el cierre de sesión de un usuario."""
        # Crear una solicitud simulada con sesión
        request = self.factory.get('/')
        
        # Usar un objeto de sesión real
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        # Crear un usuario de prueba
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        request.user = user
        
        # Configurar el mock para que no haga nada
        mock_logout.return_value = None
        
        # Llamar al método de logout
        self.repository.logout_user(request)
        
        # Verificar que se llamó a la función de logout de Django
        mock_logout.assert_called_once_with(request)
    
    @patch('django.contrib.auth.get_user_model')
    def test_create_user_database_error(self, mock_user_model):
        """Prueba el manejo de errores de base de datos en create_user."""
        # Configurar el mock para simular un error de base de datos
        mock_user_model.return_value = User
        with patch.object(User.objects, 'create_user') as mock_create:
            mock_create.side_effect = Exception("Error de base de datos")
            
            # Intentar crear usuario
            with self.assertRaises(Exception) as context:
                self.repository.create_user(
                    'testuser',
                    'test@example.com',
                    'testpass123'
                )
            
            self.assertIn('Error en la base de datos', str(context.exception))
    
    @patch('django.contrib.auth.authenticate')
    def test_authenticate_user_database_error(self, mock_authenticate):
        """Prueba el manejo de errores de base de datos en authenticate_user."""
        # Configurar el mock para simular un error de base de datos
        mock_authenticate.side_effect = Exception("Error de autenticación")
        
        # Mock para User.objects.get
        with patch.object(User.objects, 'get') as mock_get:
            mock_get.side_effect = Exception("Error de base de datos")
            
            # Intentar autenticar
            with self.assertRaises(Exception) as context:
                self.repository.authenticate_user('testuser', 'testpass123')
            
            self.assertIn('Error durante la autenticación', str(context.exception))
    
    @patch('django.contrib.auth.logout')
    def test_logout_user_error_handling(self, mock_logout):
        """Prueba el manejo de errores en logout_user."""
        # Configurar el mock para lanzar una excepción
        mock_logout.side_effect = Exception("Error al cerrar sesión")
        
        # Crear una solicitud simulada
        request = self.factory.get('/')
        request.user = MagicMock()
        
        # Verificar que se lanza la excepción con el mensaje correcto
        with self.assertRaises(Exception) as context:
            self.repository.logout_user(request)
        
        self.assertIn('Error al cerrar la sesión', str(context.exception))


# Mantener la clase existente para compatibilidad
class Core_authAdapterTests(TestCase):
    """Clase de prueba obsoleta, mantenida para compatibilidad."""
    def test_core_auth_model(self):
        """Prueba de compatibilidad."""
        pass