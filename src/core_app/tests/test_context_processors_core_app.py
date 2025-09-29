import pytest
from django.test import RequestFactory, override_settings
from django.urls import NoReverseMatch
from core_app.context_processors import coverage

pytestmark = pytest.mark.django_db


def make_request(path="/"):
    rf = RequestFactory()
    return rf.get(path)


@override_settings(DEBUG=False, COVERAGE_VIEW_ENABLED=False)
def test_coverage_context_disabled():
    ctx = coverage(make_request())
    assert ctx["coverage_available"] is False
    assert ctx["coverage_url"] is None


@override_settings(DEBUG=True, COVERAGE_VIEW_ENABLED=None)
def test_coverage_context_enabled_via_debug(monkeypatch):
    # Simular fallo de reverse para cubrir rama except
    def boom(name):
        raise NoReverseMatch("no route")

    import core_app.context_processors as m

    monkeypatch.setattr(m, "reverse", boom)

    ctx = coverage(make_request())
    assert ctx["coverage_available"] is True
    assert ctx["coverage_url"] is None


@override_settings(DEBUG=False, COVERAGE_VIEW_ENABLED=True)
def test_coverage_context_enabled_and_url(monkeypatch):
    # Simular reverse exitoso
    monkeypatch.setattr(
        "core_app.context_processors.reverse", lambda name: "/coverage/"
    )
    ctx = coverage(make_request())
    assert ctx["coverage_available"] is True
    assert ctx["coverage_url"] == "/coverage/"
