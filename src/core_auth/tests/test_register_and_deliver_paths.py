import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import reverse
from unittest.mock import patch

from core_auth.adapters.views import RegisterView, deliver_reset_request
from core_auth.models import PasswordResetRequest, CoreAuthProfile

User = get_user_model()


def attach_messages(request):
    setattr(request, 'session', {})
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)


@pytest.mark.django_db
class TestRegisterCaseInsensitiveDuplicate:
    def test_duplicate_email_case_insensitive_in_view(self):
        # Crear usuario existente con email en minúsculas
        User.objects.create_user(username='uexist', email='dup@example.com', password='x')
        factory = RequestFactory()
        # Enviar el mismo email con distinto casing para que pase clean_email
        data = {
            'username': 'nuevo',
            'email': 'DUP@example.com',  # clean_email no lo detecta (usa match exacto), la vista sí (iexact)
            'password1': 'Secret123!','password2': 'Secret123!',
            'terms': True,
        }
        request = factory.post(reverse('core_auth:register'), data)
        attach_messages(request)
        response = RegisterView.as_view()(request)
        # No redirige, se renderiza con error, cubre líneas 58-59
        assert response.status_code == 200


@pytest.mark.django_db
class TestDeliverSuccessPath:
    def _staff_request(self, path):
        factory = RequestFactory()
        req = factory.get(path)
        user = User.objects.create_user('admin', password='x', is_staff=True, is_active=True)
        req.user = user
        attach_messages(req)
        return req

    def test_deliver_success_sets_password_and_profile_and_resolves(self):
        # Preparar solicitud en estado listo con usuario y password preview
        target_user = User.objects.create_user('john', password='oldpass')
        prr = PasswordResetRequest.objects.create(
            identifier_submitted='john',
            status='ready_to_deliver',
            user=target_user,
        )
        prr.temp_password_preview = 'TMPpass123'
        prr.save()

        req = self._staff_request(reverse('core_auth:staff_reset_request_deliver', args=[prr.pk]))
        resp = deliver_reset_request(req, prr.pk)
        assert resp.status_code == 302

        # Verificar efectos: user password cambiada, profile.must_change_password True, status resolved
        target_user.refresh_from_db()
        assert target_user.check_password('TMPpass123')

        profile = CoreAuthProfile.objects.get(user=target_user)
        assert profile.must_change_password is True

        prr.refresh_from_db()
        assert prr.status == 'resolved'
        assert prr.delivered_at is not None
