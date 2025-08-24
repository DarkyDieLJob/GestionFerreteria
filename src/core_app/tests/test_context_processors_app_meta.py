import os
import io
import pytest
from django.test import RequestFactory, override_settings
from core_app.context_processors import app_meta

pytestmark = pytest.mark.django_db


def make_request(path="/"):
    rf = RequestFactory()
    return rf.get(path)


def _write_changelog(repo_root: str, content: str) -> str:
    path = os.path.join(repo_root, "CHANGELOG.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


@override_settings(NOMBRE_APLICACION="Mi App Test")
def test_app_meta_fallback_dev_when_no_changelog(tmp_path, settings):
    # Estructura: tmp/src como BASE_DIR; CHANGELOG se busca en repo_root = parent(BASE_DIR)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    settings.BASE_DIR = str(src_dir)

    ctx = app_meta(make_request())
    assert ctx["app_name"] == "Mi App Test"
    assert ctx["app_version"] == "dev"


@override_settings(NOMBRE_APLICACION="Mi App Test")
def test_app_meta_reads_version_from_changelog_v_prefix(tmp_path, settings):
    # Crear repo_root y archivo CHANGELOG con encabezado '## v1.2.3'
    repo_root = tmp_path
    src_dir = repo_root / "src"
    src_dir.mkdir()
    settings.BASE_DIR = str(src_dir)

    _write_changelog(
        str(repo_root),
        """\
# Changelog

## v1.2.3 - 2025-08-10
- Something

## v1.2.2 - 2025-08-01
- Older
""",
    )

    ctx = app_meta(make_request())
    assert ctx["app_name"] == "Mi App Test"
    assert ctx["app_version"] == "1.2.3"


@override_settings(NOMBRE_APLICACION="Mi App Test")
def test_app_meta_reads_version_with_brackets_header(tmp_path, settings):
    # Encabezado '## [2.0.0] - ...' también debe ser reconocido
    repo_root = tmp_path
    src_dir = repo_root / "src"
    src_dir.mkdir()
    settings.BASE_DIR = str(src_dir)

    _write_changelog(
        str(repo_root),
        """\
# Changelog

## [2.0.0] - 2025-08-10
- Major

## [1.9.9] - 2025-08-01
- Older
""",
    )

    ctx = app_meta(make_request())
    assert ctx["app_name"] == "Mi App Test"
    assert ctx["app_version"] == "2.0.0"
