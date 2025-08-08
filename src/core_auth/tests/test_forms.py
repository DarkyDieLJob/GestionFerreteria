"""Tests for core_auth forms."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from core_auth.adapters.forms import RegisterForm, LoginForm

User = get_user_model()


class TestLoginForm(TestCase):
    """Test cases for LoginForm."""
    
    def test_form_fields(self):
        """Test that the form has the expected fields."""
        form = LoginForm()
        self.assertIn('username', form.fields)
        self.assertIn('password', form.fields)
        self.assertIn('remember_me', form.fields)
        
        # Check widget attributes
        self.assertEqual(
            form.fields['username'].widget.attrs['class'],
            'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm'
        )
        self.assertEqual(
            form.fields['password'].widget.attrs['class'],
            'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm'
        )
        self.assertEqual(
            form.fields['remember_me'].widget.attrs['class'],
            'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        )


class TestRegisterForm(TestCase):
    """Test cases for RegisterForm."""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )
    
    def test_form_fields(self):
        """Test that the form has the expected fields."""
        form = RegisterForm()
        self.assertIn('email', form.fields)
        self.assertIn('username', form.fields)
        self.assertIn('password1', form.fields)
        self.assertIn('password2', form.fields)
        self.assertIn('terms', form.fields)
        
        # Check required fields
        self.assertTrue(form.fields['email'].required)
        self.assertTrue(form.fields['username'].required)
        self.assertTrue(form.fields['password1'].required)
        self.assertTrue(form.fields['password2'].required)
        self.assertTrue(form.fields['terms'].required)
    
    def test_clean_email_unique(self):
        """Test that email validation works for duplicate emails."""
        form = RegisterForm(data={
            'email': 'existing@example.com',  # Already exists
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'terms': 'on'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(
            form.errors['email'][0],
            'Ya existe un usuario con este correo electrónico.'
        )
    
    def test_clean_username_unique(self):
        """Test that username validation works for duplicate usernames."""
        form = RegisterForm(data={
            'email': 'new@example.com',
            'username': 'existinguser',  # Already exists
            'password1': 'testpass123',
            'password2': 'testpass123',
            'terms': 'on'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertEqual(
            form.errors['username'][0],
            'Este nombre de usuario ya está en uso.'
        )
    
    def test_clean_terms_required(self):
        """Test that terms must be accepted."""
        form = RegisterForm(data={
            'email': 'new@example.com',
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
            # Missing terms
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('terms', form.errors)
        self.assertEqual(
            form.errors['terms'][0],
            'Debes aceptar los términos y condiciones para registrarte.'
        )
    
    def test_clean_success(self):
        """Test successful form validation."""
        form = RegisterForm(data={
            'email': 'new@example.com',
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'terms': 'on'
        })
        
        self.assertTrue(form.is_valid())
        
        # Test saving the form
        user = form.save()
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.username, 'newuser')
        self.assertTrue(user.check_password('testpass123'))
