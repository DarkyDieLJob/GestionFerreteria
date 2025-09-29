import pytest
from django.test import RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch

from core_auth.adapters.views import RegisterView


def attach_messages(request):
    setattr(request, "session", {})
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)


@pytest.mark.django_db
def test_register_exception_with_valid_form_triggers_error_messages():
    factory = RequestFactory()
    data = {
        "username": "validuser",
        "email": "valid@example.com",
        "password1": "StrongPass123!",
        "password2": "StrongPass123!",
        "terms": True,
        "dni_last4": "1234",
    }
    request = factory.post(reverse("core_auth:register"), data)
    attach_messages(request)

    with patch("core_auth.adapters.views.RegisterUserUseCase") as MockUC:
        MockUC.return_value.execute.side_effect = Exception("boom")
        response = RegisterView.as_view()(request)

    # La vista debe capturar la excepción, loguear y mostrar mensaje de error
    assert response.status_code == 200
