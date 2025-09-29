import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model

from core_auth.context_processors import staff_reset_requests_badge

pytestmark = pytest.mark.django_db


class _DummyQS:
    def filter(self, *args, **kwargs):
        raise Exception("boom")


class _DummyManager:
    def select_related(self, *args, **kwargs):
        return _DummyQS()


class _DummyModel:
    objects = _DummyManager()


def test_staff_reset_requests_badge_handles_exceptions(monkeypatch):
    # Monkeypatch del modelo para provocar excepción en el queryset
    import core_auth.context_processors as m
    monkeypatch.setattr(m, "PasswordResetRequest", _DummyModel)

    User = get_user_model()
    staff = User.objects.create_user(
        username="s1", email="s1@example.com", password="pass1234", is_staff=True
    )

    rf = RequestFactory()
    request = rf.get("/")
    request.user = staff

    ctx = staff_reset_requests_badge(request)
    assert ctx["pending_reset_requests_count"] == 0
