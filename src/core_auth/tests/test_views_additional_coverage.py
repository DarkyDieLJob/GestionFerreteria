import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import reverse
from unittest.mock import patch, MagicMock

from core_auth.adapters.views import (
    RegisterView,
    ResetRequestListView,
    approve_reset_request,
    deliver_reset_request,
    LogoutView,
)
from core_auth.models import PasswordResetRequest, CoreAuthProfile

User = get_user_model()


def attach_messages(request):
    # Mensajería para RequestFactory
    setattr(request, "session", {})
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)


@pytest.mark.django_db
class TestRegisterViewExtra:
    def test_register_duplicate_email_adds_error(self):
        # Usuario existente con ese email
        User.objects.create_user(username="u1", email="dup@example.com", password="x")
        factory = RequestFactory()
        data = {
            "username": "nuevo",
            "email": "dup@example.com",
            "password1": "Secret123!",
            "password2": "Secret123!",
        }
        request = factory.post(reverse("core_auth:register"), data)
        attach_messages(request)
        response = RegisterView.as_view()(request)
        assert response.status_code == 200
        # El template recibe el form con error (no validamos template, solo que no redirige)

    def test_register_exception_path(self):
        factory = RequestFactory()
        data = {
            "username": "nuevo2",
            "email": "ok@example.com",
            "password1": "Secret123!",
            "password2": "Secret123!",
        }
        request = factory.post(reverse("core_auth:register"), data)
        attach_messages(request)
        # Patch al caso de uso para provocar excepción
        with patch("core_auth.adapters.views.RegisterUserUseCase") as MockUC:
            MockUC.return_value.execute.side_effect = Exception("boom")
            response = RegisterView.as_view()(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestResetRequestListViewScopes:
    def test_scope_all_lists_all(self):
        u = User.objects.create_user("staff", password="x", is_staff=True)
        # Crear varias solicitudes
        PasswordResetRequest.objects.create(identifier_submitted="a", status="pending")
        PasswordResetRequest.objects.create(identifier_submitted="b", status="approved")
        factory = RequestFactory()
        request = factory.get(reverse("core_auth:staff_reset_requests") + "?scope=all")
        request.user = u
        attach_messages(request)
        response = ResetRequestListView.as_view()(request)
        assert response.status_code == 200

    def test_status_filter_applies(self):
        u = User.objects.create_user("staff2", password="x", is_staff=True)
        PasswordResetRequest.objects.create(identifier_submitted="a", status="pending")
        PasswordResetRequest.objects.create(identifier_submitted="b", status="approved")
        factory = RequestFactory()
        request = factory.get(
            reverse("core_auth:staff_reset_requests") + "?status=pending"
        )
        request.user = u
        attach_messages(request)
        response = ResetRequestListView.as_view()(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestApproveAndDeliverErrors:
    def _staff_request(self, path):
        factory = RequestFactory()
        req = factory.get(path)
        # staff_member_required requiere user.staff y user.is_active
        user = User.objects.create_user(
            "admin", password="x", is_staff=True, is_active=True
        )
        req.user = user
        attach_messages(req)
        return req

    def test_approve_reset_request_invalid_status(self):
        # Estado no permitido debe mostrar error y redirigir
        prr = PasswordResetRequest.objects.create(
            identifier_submitted="x", status="resolved"
        )
        req = self._staff_request(
            reverse("core_auth:staff_reset_request_approve", args=[prr.pk])
        )
        resp = approve_reset_request(req, prr.pk)
        assert resp.status_code == 302

    def test_deliver_requires_ready_status(self):
        prr = PasswordResetRequest.objects.create(
            identifier_submitted="x", status="pending"
        )
        req = self._staff_request(
            reverse("core_auth:staff_reset_request_deliver", args=[prr.pk])
        )
        resp = deliver_reset_request(req, prr.pk)
        assert resp.status_code == 302

    def test_deliver_requires_user(self):
        prr = PasswordResetRequest.objects.create(
            identifier_submitted="x", status="ready_to_deliver"
        )
        prr.temp_password_preview = "TMP123"
        prr.save()
        req = self._staff_request(
            reverse("core_auth:staff_reset_request_deliver", args=[prr.pk])
        )
        resp = deliver_reset_request(req, prr.pk)
        assert resp.status_code == 302

    def test_deliver_requires_temp_password(self):
        # Con user pero sin preview
        user = User.objects.create_user("uu", password="x")
        prr = PasswordResetRequest.objects.create(
            identifier_submitted="x", status="ready_to_deliver", user=user
        )
        req = self._staff_request(
            reverse("core_auth:staff_reset_request_deliver", args=[prr.pk])
        )
        resp = deliver_reset_request(req, prr.pk)
        assert resp.status_code == 302


@pytest.mark.django_db
class TestLogoutException:
    def test_logout_exception_branch(self):
        # Forzar excepción dentro del caso de uso
        u = User.objects.create_user("uu2", password="x")
        factory = RequestFactory()
        request = factory.get(reverse("core_auth:logout"))
        request.user = u
        attach_messages(request)
        with patch("core_auth.adapters.views.LogoutUserUseCase") as MockUC:
            MockUC.return_value.execute.side_effect = Exception("boom")
            resp = LogoutView.as_view()(request)
        assert resp.status_code == 302
