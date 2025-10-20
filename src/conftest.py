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
@pytest.fixture(scope="session", autouse=True)
def log_database_state(pytestconfig, django_db_setup, django_db_blocker):
    """Log database configuration and available tables for diagnostics."""
    from django.conf import settings
    from django.db import connections

    header = "[DB-DEBUG]"
    print(f"\n{header} Django settings module: {os.getenv('DJANGO_SETTINGS_MODULE')}")
    db_summary = {alias: {"ENGINE": cfg.get("ENGINE"), "NAME": cfg.get("NAME")}
                  for alias, cfg in settings.DATABASES.items()}
    print(f"{header} settings.DATABASES summary: {db_summary}")

    with django_db_blocker.unblock():
        for alias in connections:
            conn = connections[alias]
            vendor = conn.vendor
            name = conn.settings_dict.get("NAME")
            print(f"{header} Inspecting alias='{alias}' vendor='{vendor}' name='{name}'")
            try:
                tables = conn.introspection.table_names()
            except Exception as exc:  # pragma: no cover - diagnostic path
                print(f"{header} ERROR alias='{alias}' introspection failed: {exc!r}")
            else:
                sample = tables[:10]
                extra = len(tables) - len(sample)
                print(f"{header} alias='{alias}' tables={sample}{' ...' if extra > 0 else ''} (total={len(tables)})")

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
