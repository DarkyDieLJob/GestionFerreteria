from pathlib import Path
import io
import os
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client, override_settings
from django.conf import settings

User = get_user_model()

pytestmark = pytest.mark.django_db


def make_staff_user():
    return User.objects.create_user(
        username="staff",
        email="staff@example.com",
        password="pass1234",
        is_staff=True,
    )


def make_normal_user():
    return User.objects.create_user(
        username="normal",
        email="normal@example.com",
        password="pass1234",
        is_staff=False,
    )


@override_settings(COVERAGE_VIEW_ENABLED=False)
def test_coverage_report_disabled_returns_404():
    client = Client()
    user = make_staff_user()
    client.force_login(user)

    resp = client.get(reverse("core_app:coverage"))
    assert resp.status_code == 404


def test_coverage_report_enabled_but_missing_index_returns_404(tmp_path, settings):
    # Simular BASE_DIR apuntando a un directorio temporal (como si fuera src/)
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    settings.COVERAGE_VIEW_ENABLED = True
    settings.BASE_DIR = str(fake_src)

    client = Client()
    user = make_staff_user()
    client.force_login(user)

    # No creamos htmlcov/index.html => 404
    resp = client.get(reverse("core_app:coverage"))
    assert resp.status_code == 404


def test_coverage_report_enabled_serves_index_with_base_injected(tmp_path, settings):
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    htmlcov = tmp_path / "htmlcov"
    htmlcov.mkdir()
    index = htmlcov / "index.html"
    index.write_text(
        "<html><head><title>cov</title></head><body>ok</body></html>", encoding="utf-8"
    )

    settings.COVERAGE_VIEW_ENABLED = True
    settings.BASE_DIR = str(fake_src)

    client = Client()
    user = make_staff_user()
    client.force_login(user)

    resp = client.get(reverse("core_app:coverage"))
    assert resp.status_code == 200
    body = resp.content.decode("utf-8")
    # Debe inyectar <base href="/coverage/raw/">
    assert '<base href="/coverage/raw/">' in body
    assert "cov" in body


def test_coverage_asset_serves_file(tmp_path, settings):
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    htmlcov = tmp_path / "htmlcov"
    htmlcov.mkdir()
    css = htmlcov / "style.css"
    css.write_text("body{color:black}", encoding="utf-8")

    settings.COVERAGE_VIEW_ENABLED = True
    settings.BASE_DIR = str(fake_src)

    client = Client()
    user = make_staff_user()
    client.force_login(user)

    resp = client.get(reverse("core_app:coverage_asset", args=["style.css"]))
    assert resp.status_code == 200
    content = resp.getvalue() if hasattr(resp, "getvalue") else b"".join(resp)
    assert b"color" in content


def test_coverage_asset_blocks_path_traversal(tmp_path, settings):
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    htmlcov = tmp_path / "htmlcov"
    htmlcov.mkdir()

    settings.COVERAGE_VIEW_ENABLED = True
    settings.BASE_DIR = str(fake_src)

    client = Client()
    user = make_staff_user()
    client.force_login(user)

    # Intento de traversal
    resp = client.get(reverse("core_app:coverage_asset", args=["../secret.txt"]))
    assert resp.status_code == 404


def test_coverage_raw_serves_html(tmp_path, settings):
    fake_src = tmp_path / "src"
    fake_src.mkdir()
    htmlcov = tmp_path / "htmlcov"
    htmlcov.mkdir()
    other = htmlcov / "details.html"
    other.write_text("<html><body>details</body></html>", encoding="utf-8")

    settings.COVERAGE_VIEW_ENABLED = True
    settings.BASE_DIR = str(fake_src)

    client = Client()
    user = make_staff_user()
    client.force_login(user)

    resp = client.get(reverse("core_app:coverage_raw", args=["details.html"]))
    assert resp.status_code == 200
    content = resp.getvalue() if hasattr(resp, "getvalue") else b"".join(resp)
    assert b"details" in content


def test_home_requires_login_and_renders_context():
    client = Client()
    # sin login, redirige al login
    resp = client.get(reverse("core_app:home"))
    assert resp.status_code in (302, 301)

    # con login
    user = make_normal_user()
    client.force_login(user)
    resp = client.get(reverse("core_app:home"))
    assert resp.status_code == 200
    assert user.username in resp.content.decode("utf-8")
