import pytest
from unittest.mock import patch, mock_open
from django.test import RequestFactory
from core_app.context_processors import app_meta


@pytest.mark.django_db
def test_app_meta_exception_sets_dev_version():
    rf = RequestFactory()
    request = rf.get("/")

    # Forzar que encuentre un CHANGELOG.md pero que abrirlo lance excepción
    with patch("core_app.context_processors.os.path.exists", return_value=True), patch(
        "core_app.context_processors.open", mock_open(), create=True
    ) as m_open:
        m_open.side_effect = Exception("read error")
        ctx = app_meta(request)

    assert ctx["app_version"] == "dev"
