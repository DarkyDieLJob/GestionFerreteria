import os
import sys
import pytest
from pathlib import Path
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from importlib import import_module

# Ensure our local pytest plugin is loaded
pytest_plugins = ["pytest_cov_apps"]

# ---------------------------------------------------------------------------
# Dynamic coverage selection based on INSTALLED_APPS
# ---------------------------------------------------------------------------

def pytest_load_initial_conftests(parser, args):
    """
    Before pytest parses CLI args, dynamically add --cov targets for first-party
    Django apps listed in INSTALLED_APPS. This ensures the HTML coverage report
    reflects the apps actually installed in this project without hardcoding in
    pytest.ini.

    Behavior:
    - If the user already passed any --cov flag, do nothing (respect manual choice).
    - Otherwise, import Django settings and collect app labels whose import
      modules live under the project src/ directory (first-party heuristic).
    - Append --cov=<app> for each collected app to args.

    You can override behavior via env var COV_APPS_MODE:
      - 'installed' (default): include first-party INSTALLED_APPS under src/
      - 'core': only include core_app and core_auth
      - 'all': include all INSTALLED_APPS that resolve to local modules under src/
               (same as 'installed' here; kept for future differentiation)
    """
    # Respect explicit user choice if any --cov is present
    if any(str(a).startswith("--cov") for a in args):
        return

    # Ensure settings are available
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_config.test_settings")
    try:
        import django
        django.setup()
    except Exception:
        # If setup fails, skip dynamic injection to avoid breaking pytest
        return

    from django.conf import settings as dj_settings

    mode = os.environ.get("COV_APPS_MODE", "installed").lower()

    # Project base dirs
    repo_root = Path(__file__).resolve().parent.parent  # points to repo/src
    src_dir = repo_root  # manage.py lives in src/

    def is_first_party(module_name: str) -> bool:
        try:
            mod = import_module(module_name)
            path = Path(getattr(mod, "__file__", "")).resolve()
        except Exception:
            return False
        # Consider first-party if module file lives under our src directory
        try:
            path.relative_to(src_dir)
            return True
        except Exception:
            return False

    apps = []
    if mode == "core":
        candidates = ["core_app", "core_auth"]
    else:
        candidates = list(dj_settings.INSTALLED_APPS)

    for app in candidates:
        # Normalize dotted app config like 'app.apps.Config' -> 'app'
        app_root = app.split(".apps.")[0]
        # Skip Django/third-party that are not under src
        if is_first_party(app_root):
            apps.append(app_root)

    # De-duplicate and keep stable order
    seen = set()
    cov_targets = [a for a in apps if not (a in seen or seen.add(a))]

    # Append --cov for each local app
    for app in cov_targets:
        args.append(f"--cov={app}")

# Add src directory to PYTHONPATH
root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))

# Set default Django settings module for tests
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_config.test_settings")

# Fixtures
@pytest.fixture(scope="session", autouse=True)
def _apply_migrations_for_tests(django_db_setup, django_db_blocker):
    """Ensure DB tables exist even when migrations are disabled.

    In CI we disable migrations to avoid relying on migration files. This fixture
    forces Django to create tables using migrate --run-syncdb before any test runs.
    """
    from django.core.management import call_command
    with django_db_blocker.unblock():
        call_command("migrate", run_syncdb=True, interactive=False, verbosity=0)
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
def auth_client(client, db, user):
    """Create an authenticated test client."""
    client.force_login(user)
    return client

@pytest.fixture
def rf():
    """RequestFactory instance."""
    return RequestFactory()
