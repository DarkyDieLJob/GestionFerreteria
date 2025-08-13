import os
import sys
import pytest
from pathlib import Path
from django.contrib.auth import get_user_model
from django.test import RequestFactory

# Add src directory to PYTHONPATH
root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_config.settings")

# Pytest configuration
def pytest_configure():
    from django.conf import settings, settings as django_settings
    from django.core.exceptions import ImproperlyConfigured
    
    try:
        # Check if Django is already configured
        settings.configured
    except (RuntimeError, ImproperlyConfigured):
        # Minimum test configuration
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
                'core_auth',
                'core_app',
            ],
            SECRET_KEY='test-secret-key',
            MIDDLEWARE=[
                'django.middleware.security.SecurityMiddleware',
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.middleware.clickjacking.XFrameOptionsMiddleware',
            ],
            TEMPLATES=[
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [],
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'context_processors': [
                            'django.template.context_processors.debug',
                            'django.template.context_processors.request',
                            'django.contrib.auth.context_processors.auth',
                            'django.contrib.messages.context_processors.messages',
                        ],
                    },
                },
            ],
            ROOT_URLCONF='core_config.urls',
            LOGIN_REDIRECT_URL='dashboard',  # Ensure login redirects to dashboard
        )
        
        # Initialize Django
        import django
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
