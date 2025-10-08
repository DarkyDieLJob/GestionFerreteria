import os
import sys
import pytest
from pathlib import Path
from django.contrib.auth import get_user_model
from django.test import RequestFactory

# Add src directory to PYTHONPATH
root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))

# Set default Django settings module for pytest runs
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_config.test_settings")

# Pytest configuration
def pytest_configure():
    from django.conf import settings
    import django

    if not settings.configured:
        django.setup()

# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        is_active=True
    )

@pytest.fixture
def admin_user():
    """Create a test admin user."""
    User = get_user_model()
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        is_active=True
    )

@pytest.fixture
def client():
    """Create a test client."""
    from django.test import Client
    return Client()

@pytest.fixture
def auth_client(client, user):
    """Create an authenticated test client."""
    client.force_login(user)
    return client

@pytest.fixture
def rf():
    """RequestFactory instance."""
    return RequestFactory()
