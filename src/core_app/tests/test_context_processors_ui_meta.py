import os
import pytest
from django.test import RequestFactory, override_settings
from core_app.context_processors import ui_meta

pytestmark = pytest.mark.django_db


def make_request(path="/"):
    rf = RequestFactory()
    return rf.get(path)


@override_settings(NOMBRE_APLICACION="Mi App Test")
def test_ui_meta_prefers_env_app_version(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    # Toggle variations
    monkeypatch.setenv("SHOW_PROJECT_VERSION", "true")
    monkeypatch.setenv("SHOW_TEMPLATE_ATTRIB", "true")
    monkeypatch.setenv("TEMPLATE_ATTRIB_MINIMAL", "false")
    ctx = ui_meta(make_request())
    assert ctx["app_name"] == "Mi App Test"
    assert ctx["app_version"] == "9.9.9"
    # Template meta should be imported from src/template_meta.py
    assert ctx["template_name"]
    assert ctx["template_version"]
    assert ctx["show_project_version"] is True
    assert ctx["show_template_attrib"] is True
    assert ctx["template_attrib_minimal"] is False


@override_settings(NOMBRE_APLICACION="Mi App Test")
def test_ui_meta_reads_version_from_changelog_when_no_env(
    tmp_path, settings, monkeypatch
):
    # Clear APP_VERSION to force changelog path
    monkeypatch.delenv("APP_VERSION", raising=False)
    # Create repo_root/tmp/src structure and a CHANGELOG.md with a version
    repo_root = tmp_path
    src_dir = repo_root / "src"
    src_dir.mkdir()
    settings.BASE_DIR = str(src_dir)
    changelog = repo_root / "CHANGELOG.md"
    changelog.write_text(
        """
# Changelog

## v2.3.4 - 2026-01-01
- Entry
""".strip(),
        encoding="utf-8",
    )

    ctx = ui_meta(make_request())
    assert ctx["app_name"] == "Mi App Test"
    assert ctx["app_version"] == "2.3.4"
    # Defaults for toggles (no env provided)
    assert ctx["show_project_version"] is True
    assert ctx["show_template_attrib"] is True
    assert ctx["template_attrib_minimal"] is False
    assert ctx["show_template_version_in_nav"] is False
    assert ctx["show_footer_year"] is True


@override_settings(NOMBRE_APLICACION="Mi App Test")
def test_ui_meta_toggle_overrides(monkeypatch):
    # Flip all toggles to exercise branches
    monkeypatch.setenv("SHOW_PROJECT_VERSION", "0")
    monkeypatch.setenv("SHOW_TEMPLATE_ATTRIB", "no")
    monkeypatch.setenv("TEMPLATE_ATTRIB_MINIMAL", "yes")
    monkeypatch.setenv("SHOW_TEMPLATE_VERSION_IN_NAV", "on")
    monkeypatch.setenv("SHOW_FOOTER_YEAR", "false")
    # Provide APP_VERSION to avoid changelog lookup path in this test
    monkeypatch.setenv("APP_VERSION", "1.0.0")

    ctx = ui_meta(make_request())
    assert ctx["app_version"] == "1.0.0"
    assert ctx["show_project_version"] is False
    assert ctx["show_template_attrib"] is False
    assert ctx["template_attrib_minimal"] is True
    assert ctx["show_template_version_in_nav"] is True
    assert ctx["show_footer_year"] is False
