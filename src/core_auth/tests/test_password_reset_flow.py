import pytest
from django.urls import reverse
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model

from core_auth.models import CoreAuthProfile, PasswordResetRequest


@pytest.mark.django_db
class TestForgotPasswordInfoView:
    def test_get_page_ok(self, client):
        url = reverse('core_auth:forgot_password_info')
        resp = client.get(url)
        assert resp.status_code == 200
        assert '¿Olvidaste tu contraseña?' in resp.content.decode()

    def test_post_creates_reset_request_and_associates_user(self, client):
        User = get_user_model()
        user = User.objects.create_user(username='john', email='john@example.com', password='Secret123!')
        url = reverse('core_auth:forgot_password_info')

        resp = client.post(url, {'identifier': 'john'}, follow=True)
        assert resp.status_code == 200

        prrs = PasswordResetRequest.objects.all()
        assert prrs.count() == 1
        prr = prrs.first()
        assert prr.identifier_submitted == 'john'
        assert prr.user == user
        assert prr.status == 'pending'

    def test_post_with_empty_identifier_shows_error_and_creates_nothing(self, client):
        url = reverse('core_auth:forgot_password_info')
        before = PasswordResetRequest.objects.count()
        resp = client.post(url, {'identifier': ''}, follow=True)
        assert resp.status_code == 200
        after = PasswordResetRequest.objects.count()
        assert after == before

    def test_post_with_unknown_user_creates_request_without_user(self, client):
        url = reverse('core_auth:forgot_password_info')
        resp = client.post(url, {'identifier': 'noexiste'}, follow=True)
        assert resp.status_code == 200
        prr = PasswordResetRequest.objects.latest('created_at')
        assert prr.identifier_submitted == 'noexiste'
        assert prr.user is None
        assert prr.status == 'pending'


@pytest.mark.django_db
class TestStaffResetRequestViews:
    @pytest.fixture(autouse=True)
    def setup(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username='admin', email='admin@example.com', password='Admin123!', is_staff=True
        )
        self.user = User.objects.create_user(
            username='alice', email='alice@example.com', password='AlicePass123!'
        )
        self.prr = PasswordResetRequest.objects.create(
            user=self.user, identifier_submitted='alice', status='pending'
        )
        self.list_url = reverse('core_auth:staff_reset_requests')
        self.detail_url = reverse('core_auth:staff_reset_request_detail', args=[self.prr.id])
        self.approve_url = reverse('core_auth:staff_reset_request_approve', args=[self.prr.id])

    def test_list_requires_staff(self, client):
        resp = client.get(self.list_url)
        assert resp.status_code in (302, 301)
        assert reverse('core_auth:login') in resp.url

    def test_list_ok_for_staff(self, client):
        client.force_login(self.staff)
        resp = client.get(self.list_url)
        assert resp.status_code == 200
        assert 'Solicitudes de reseteo' in resp.content.decode()

    def test_detail_ok_for_staff(self, client):
        client.force_login(self.staff)
        resp = client.get(self.detail_url)
        assert resp.status_code == 200
        assert f"#{self.prr.id}" in resp.content.decode()

    def test_approve_generates_temp_and_sets_flag(self, client):
        client.force_login(self.staff)
        resp = client.get(self.approve_url, follow=True)
        assert resp.status_code == 200
        prr = PasswordResetRequest.objects.get(id=self.prr.id)
        assert prr.status == 'processed'
        assert prr.processed_by == self.staff
        assert prr.temp_password_preview

        # User should have must_change_password = True
        profile = CoreAuthProfile.objects.get(user=self.user)
        assert profile.must_change_password is True

        # Password actually changed to the preview
        self.user.refresh_from_db()
        assert check_password(prr.temp_password_preview, self.user.password)

    def test_approve_requires_staff(self, client):
        resp = client.get(self.approve_url)
        assert resp.status_code in (302, 301)
        # Depending on decorator used, it may redirect to admin login
        assert (reverse('core_auth:login') in resp.url) or (reverse('admin:login') in resp.url)


@pytest.mark.django_db
class TestForcePasswordChangeMiddleware:
    @pytest.fixture(autouse=True)
    def setup(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='bob', email='bob@example.com', password='BobStrong123!'
        )
        profile, _ = CoreAuthProfile.objects.get_or_create(user=self.user)
        profile.must_change_password = True
        profile.save()
        self.enforced_url = reverse('core_auth:password_change_enforced')
        self.home_url = reverse('core_app:home')

    def test_redirects_to_change_when_flag_true(self, client):
        client.force_login(self.user)
        resp = client.get(self.home_url)
        assert resp.status_code in (302, 301)
        assert self.enforced_url in resp.url

    def test_password_change_clears_flag(self, client):
        client.force_login(self.user)
        # Get form
        get_resp = client.get(self.enforced_url)
        assert get_resp.status_code == 200

        # Post valid change
        post_resp = client.post(
            self.enforced_url,
            data={
                'old_password': 'BobStrong123!',
                'new_password1': 'BobStronger456!',
                'new_password2': 'BobStronger456!',
            },
            follow=True,
        )
        assert post_resp.status_code == 200
        profile = CoreAuthProfile.objects.get(user=self.user)
        assert profile.must_change_password is False

    def test_anonymous_user_not_redirected_by_middleware(self, client):
        # Anonymous access to home will typically redirect to login,
        # but middleware should not force to enforced_url for anonymous
        resp = client.get(self.home_url)
        assert resp.status_code in (302, 301)
        assert self.enforced_url not in resp.url

    def test_password_change_invalid_old_password_keeps_flag(self, client):
        client.force_login(self.user)
        resp = client.post(
            self.enforced_url,
            data={
                'old_password': 'wrong-old',
                'new_password1': 'NewPass123!@#',
                'new_password2': 'NewPass123!@#',
            },
            follow=True,
        )
        assert resp.status_code == 200
        profile = CoreAuthProfile.objects.get(user=self.user)
        assert profile.must_change_password is True
        # Errors should be present in form content
        assert 'incorrecta' in resp.content.decode() or 'invalid' in resp.content.decode().lower()

    def test_password_change_mismatch_new_passwords_keeps_flag(self, client):
        client.force_login(self.user)
        resp = client.post(
            self.enforced_url,
            data={
                'old_password': 'BobStrong123!',
                'new_password1': 'Mismatch123!@#',
                'new_password2': 'Mismatch123!@#DIFF',
            },
            follow=True,
        )
        assert resp.status_code == 200
        profile = CoreAuthProfile.objects.get(user=self.user)
        assert profile.must_change_password is True
        assert 'coinciden' in resp.content.decode() or 'match' in resp.content.decode().lower()

    def test_exempt_prefix_admin_path_not_forced(self, client):
        # With flag True, accessing /admin should not be forced to enforced_url by our middleware
        client.force_login(self.user)
        resp = client.get('/admin/', follow=False)
        assert resp.status_code in (302, 301)
        assert self.enforced_url not in resp.headers.get('Location', '')

    def test_exempt_named_route_password_change_not_forced(self, client):
        # Accessing the enforced view itself should not redirect (no loop)
        client.force_login(self.user)
        resp = client.get(self.enforced_url)
        assert resp.status_code == 200

    def test_unresolvable_path_does_not_crash_and_no_redirect_when_flag_false(self, client):
        # Hit the resolve exception path in middleware (coverage)
        # Set flag to False so after exception it returns None
        profile = CoreAuthProfile.objects.get(user=self.user)
        profile.must_change_password = False
        profile.save()
        client.force_login(self.user)
        resp = client.get('/__no_route__')
        # Should be a 404 from URL resolver, not a redirect to enforced
        assert resp.status_code == 404
