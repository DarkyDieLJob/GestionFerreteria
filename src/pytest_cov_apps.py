import os
from importlib import import_module
from pathlib import Path


def pytest_load_initial_conftests(parser, args):
    """
    Dynamically add --cov=<app> for first-party Django apps in INSTALLED_APPS.

    Rules:
    - If any --cov is already present, do nothing.
    - Determine first-party by module path under repo src/.
    - Controlled by COV_APPS_MODE env:
      * 'installed' (default): all local INSTALLED_APPS
      * 'core': only core_app and core_auth
    """
    if any(str(a).startswith("--cov") for a in args):
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_config.test_settings")
    try:
        import django
        django.setup()
    except Exception:
        return

    from django.conf import settings as dj_settings

    mode = os.environ.get("COV_APPS_MODE", "installed").lower()

    # Project src directory (manage.py lives in src/)
    src_dir = Path(__file__).resolve().parent

    def is_first_party(module_name: str) -> bool:
        try:
            mod = import_module(module_name)
            path = Path(getattr(mod, "__file__", "")).resolve()
        except Exception:
            return False
        try:
            path.relative_to(src_dir)
            return True
        except Exception:
            return False

    if mode == "core":
        candidates = ["core_app", "core_auth"]
    else:
        candidates = list(dj_settings.INSTALLED_APPS)

    apps = []
    for app in candidates:
        app_root = app.split(".apps.")[0]
        if is_first_party(app_root):
            apps.append(app_root)

    seen = set()
    cov_targets = [a for a in apps if not (a in seen or seen.add(a))]

    for app in cov_targets:
        args.append(f"--cov={app}")

    if os.environ.get("COV_APPS_DEBUG"):
        print("[pytest_cov_apps] Injected coverage targets:", ", ".join(cov_targets))
