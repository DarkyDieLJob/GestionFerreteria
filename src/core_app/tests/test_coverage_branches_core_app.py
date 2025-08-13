import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model


@pytest.mark.django_db
class TestCoverageBranchesCoreApp:
    def _login_staff(self, client):
        User = get_user_model()
        user = User.objects.create_user(username='staff', password='x', is_staff=True, is_superuser=True)
        client.force_login(user)

    def test_coverage_asset_not_enabled_when_setting_absent_and_debug_false(self, client, settings):
        # Ensure COVERAGE_VIEW_ENABLED is absent
        if hasattr(settings, 'COVERAGE_VIEW_ENABLED'):
            delattr(settings, 'COVERAGE_VIEW_ENABLED')
        settings.DEBUG = False
        self._login_staff(client)
        url = reverse('core_app:coverage_asset', kwargs={'path': 'foo.css'})
        resp = client.get(url)
        assert resp.status_code == 404

    def test_coverage_raw_not_enabled_when_setting_absent_and_debug_false(self, client, settings):
        if hasattr(settings, 'COVERAGE_VIEW_ENABLED'):
            delattr(settings, 'COVERAGE_VIEW_ENABLED')
        settings.DEBUG = False
        self._login_staff(client)
        url = reverse('core_app:coverage_raw', kwargs={'path': 'bar.html'})
        resp = client.get(url)
        assert resp.status_code == 404
