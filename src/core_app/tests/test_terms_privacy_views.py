import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTermsPrivacyViews:
    def test_terms_public_access_returns_200(self, client):
        url = reverse("core_app:terms")
        resp = client.get(url)
        assert resp.status_code == 200

    def test_privacy_public_access_returns_200(self, client):
        url = reverse("core_app:privacy")
        resp = client.get(url)
        assert resp.status_code == 200

    def test_terms_contains_title_and_link_to_privacy(self, client):
        url = reverse("core_app:terms")
        resp = client.get(url)
        content = resp.content.decode("utf-8")
        assert "Términos de Servicio" in content
        assert reverse("core_app:privacy") in content

    def test_privacy_contains_title_and_link_to_terms(self, client):
        url = reverse("core_app:privacy")
        resp = client.get(url)
        content = resp.content.decode("utf-8")
        assert "Política de Privacidad" in content
        assert reverse("core_app:terms") in content
