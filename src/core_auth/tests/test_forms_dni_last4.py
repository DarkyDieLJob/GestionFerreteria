import pytest
from django.contrib.auth import get_user_model

from core_auth.adapters.forms import RegisterForm

pytestmark = pytest.mark.django_db


def test_register_form_dni_last4_invalid_non_digits():
    data = {
        'username': 'newuser',
        'email': 'new@example.com',
        'password1': 'ASecurePassw0rd',
        'password2': 'ASecurePassw0rd',
        'terms': True,
        'dni_last4': '12a4',  # invalid
    }
    form = RegisterForm(data=data)
    assert not form.is_valid()
    assert 'dni_last4' in form.errors


def test_register_form_dni_last4_invalid_length():
    data = {
        'username': 'newuser2',
        'email': 'new2@example.com',
        'password1': 'ASecurePassw0rd',
        'password2': 'ASecurePassw0rd',
        'terms': True,
        'dni_last4': '123',  # invalid length
    }
    form = RegisterForm(data=data)
    assert not form.is_valid()
    assert 'dni_last4' in form.errors
