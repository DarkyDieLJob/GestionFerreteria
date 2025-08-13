import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from core_auth.adapters.repository import DjangoAuthRepository, DjangoCore_authRepository
from core_auth.adapters.models import Core_auth, PasswordResetRequest, CoreAuthProfile


@pytest.mark.django_db
class TestRepository:
    def setup_method(self):
        self.repo = DjangoAuthRepository()
        self.User = get_user_model()

    def test_create_user_success_and_authenticate_by_email(self):
        user = self.repo.create_user('u1', 'u1@example.com', 'Pass123!')
        assert user.username == 'u1'
        # authenticate by email path
        authed = self.repo.authenticate_user('u1@example.com', 'Pass123!')
        assert authed is not None and authed.pk == user.pk

    def test_create_user_duplicate_username_raises_value_error(self):
        self.User.objects.create_user(username='u2', email='u2@example.com', password='x')
        # Trigger IntegrityError for username conflict
        with pytest.raises(ValueError):
            self.repo.create_user('u2', 'other@example.com', 'Pass123!')

    def test_create_user_duplicate_email_raises_value_error(self, monkeypatch):
        # Force IntegrityError simulating unique email violation
        def fake_create_user(**kwargs):
            raise IntegrityError('unique constraint failed: email')

        monkeypatch.setattr(self.User.objects, 'create_user', lambda **kw: fake_create_user(**kw))
        with pytest.raises(ValueError):
            self.repo.create_user('u3', 'u3@example.com', 'Pass123!')

    def test_authenticate_user_invalid_returns_none(self):
        # No such user by email
        assert self.repo.authenticate_user('nosuch@example.com', 'x') is None

    def test_logout_user_does_not_raise(self):
        # Build a valid HttpRequest with session attached
        rf = RequestFactory()
        request = rf.get('/')
        # Attach session
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request.user = AnonymousUser()
        # Should not raise
        self.repo.logout_user(request)

    def test_create_user_other_integrity_error_maps_to_value_error(self, monkeypatch):
        def fake_create_user(**kwargs):
            raise IntegrityError('some other db error')

        User = self.User
        monkeypatch.setattr(User.objects, 'create_user', lambda **kw: fake_create_user(**kw))
        with pytest.raises(ValueError):
            self.repo.create_user('u4', 'u4@example.com', 'Pass123!')


@pytest.mark.django_db
def test_models_str_methods():
    # Core_auth __str__
    ca = Core_auth.objects.create(name='ItemName')
    assert str(ca) == 'ItemName'

    # PasswordResetRequest __str__ includes identifier and status
    prr = PasswordResetRequest.objects.create(identifier_submitted='idX', status='pending')
    s = str(prr)
    assert 'idX' in s and 'pending' in s


@pytest.mark.django_db
def test_profile_str_and_dummy_repository_methods():
    # Cover CoreAuthProfile.__str__
    User = get_user_model()
    u = User.objects.create_user(username='p1', email='p1@example.com', password='x')
    # Profile is auto-created by signal
    profile = u.core_profile
    assert 'Perfil(' in str(profile)

    # Cover dummy repository methods (pass statements)
    repo = DjangoCore_authRepository()
    assert repo.save({}) is None
    assert repo.get_all() is None
