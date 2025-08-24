import pytest
from django.test import Client, override_settings
from django.urls import reverse
from pathlib import Path

pytestmark = pytest.mark.django_db


def make_staff_user(django_user_model):
    return django_user_model.objects.create_user(
        username="staff2",
        email="staff2@example.com",
        password="pass1234",
        is_staff=True,
    )


@override_settings(DEBUG=True)
def test_coverage_report_enabled_via_debug_when_setting_unset(
    tmp_path, settings, django_user_model
):
    # COVERAGE_VIEW_ENABLED no definido (None) => debe usar DEBUG
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    htmlcov = tmp_path / "htmlcov"
    htmlcov.mkdir()
    index = htmlcov / "index.html"
    index.write_text(
        "<html><head><title>cov</title></head><body>ok</body></html>", encoding="utf-8"
    )

    settings.COVERAGE_VIEW_ENABLED = None
    settings.BASE_DIR = str(fake_src)

    client = Client()
    user = make_staff_user(django_user_model)
    client.force_login(user)

    resp = client.get(reverse("core_app:coverage"))
    assert resp.status_code == 200


@override_settings()
def test_coverage_report_does_not_duplicate_base_tag(
    tmp_path, settings, django_user_model
):
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    htmlcov = tmp_path / "htmlcov"
    htmlcov.mkdir()
    index = htmlcov / "index.html"
    index.write_text(
        '<html><head><base href="/coverage/raw/"></head><body>ok</body></html>',
        encoding="utf-8",
    )

    settings.COVERAGE_VIEW_ENABLED = True
    settings.BASE_DIR = str(fake_src)

    client = Client()
    user = make_staff_user(django_user_model)
    client.force_login(user)

    resp = client.get(reverse("core_app:coverage"))
    assert resp.status_code == 200
    body = resp.content.decode("utf-8")
    # Debe existir solo una etiqueta base
    assert body.count('<base href="/coverage/raw/">') == 1


@override_settings(DEBUG=False, COVERAGE_VIEW_ENABLED=False)
def test_coverage_asset_disabled_returns_404(django_user_model):
    client = Client()
    user = make_staff_user(django_user_model)
    client.force_login(user)
    resp = client.get(reverse("core_app:coverage_asset", args=["style.css"]))
    assert resp.status_code == 404


@override_settings()
def test_coverage_asset_missing_file_returns_404(tmp_path, settings, django_user_model):
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    (tmp_path / "htmlcov").mkdir()
    settings.COVERAGE_VIEW_ENABLED = True
    settings.BASE_DIR = str(fake_src)
    client = Client()
    user = make_staff_user(django_user_model)
    client.force_login(user)
    resp = client.get(reverse("core_app:coverage_asset", args=["missing.css"]))
    assert resp.status_code == 404


@override_settings(DEBUG=False, COVERAGE_VIEW_ENABLED=False)
def test_coverage_raw_disabled_returns_404(django_user_model):
    client = Client()
    user = make_staff_user(django_user_model)
    client.force_login(user)
    resp = client.get(reverse("core_app:coverage_raw", args=["details.html"]))
    assert resp.status_code == 404


@override_settings()
def test_coverage_raw_path_traversal_blocked(tmp_path, settings, django_user_model):
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    (tmp_path / "htmlcov").mkdir()
    settings.COVERAGE_VIEW_ENABLED = True
    settings.BASE_DIR = str(fake_src)
    client = Client()
    user = make_staff_user(django_user_model)
    client.force_login(user)
    resp = client.get(reverse("core_app:coverage_raw", args=["../secret.html"]))
    assert resp.status_code == 404


@override_settings()
def test_coverage_raw_missing_file_returns_404(tmp_path, settings, django_user_model):
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    (tmp_path / "htmlcov").mkdir()
    settings.COVERAGE_VIEW_ENABLED = True
    settings.BASE_DIR = str(fake_src)
    client = Client()
    user = make_staff_user(django_user_model)
    client.force_login(user)
    resp = client.get(reverse("core_app:coverage_raw", args=["missing.html"]))
    assert resp.status_code == 404
