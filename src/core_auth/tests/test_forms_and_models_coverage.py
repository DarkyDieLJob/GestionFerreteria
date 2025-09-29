import pytest
from django.contrib.auth import get_user_model
from core_auth.adapters.forms import RegisterForm
from core_auth.models import PasswordResetRequest
from unittest.mock import patch, MagicMock

User = get_user_model()


@pytest.mark.django_db
class TestRegisterFormDniValidation:
    def make_valid_data(self, **overrides):
        data = {
            "username": "userx",
            "email": "userx@example.com",
            "password1": "Secret123!",
            "password2": "Secret123!",
            "terms": True,
            "dni_last4": "1234",
        }
        data.update(overrides)
        return data

    def test_dni_last4_invalid_length(self):
        form = RegisterForm(data=self.make_valid_data(dni_last4="123"))
        assert not form.is_valid()
        # Asegura que la validación de 4 dígitos falló
        assert "dni_last4" in form.errors

    def test_dni_last4_non_digits(self):
        form = RegisterForm(data=self.make_valid_data(dni_last4="12a4"))
        assert not form.is_valid()
        assert "dni_last4" in form.errors


@pytest.mark.django_db
class TestPasswordResetRequestShortCodeFallback:
    def test_fallback_short_code_after_collisions(self):
        # Creamos el objeto sin short_code para que el save intente generarlo
        prr = PasswordResetRequest(identifier_submitted="x")

        # Simular colisiones para todas las 10 iteraciones
        class DummyQS:
            def exists(self):
                return True

        with patch(
            "core_auth.adapters.models.PasswordResetRequest.objects"
        ) as mock_mgr:
            # Para el filtro dentro del bucle, devolver algo cuyo exists() -> True
            mock_mgr.filter.return_value = DummyQS()
            # save final debe operar; llamamos al save real de models.Model vía super.
            # Para evitar dependencia del DB manager real, también proveemos create para el super().save
            mock_mgr.create = MagicMock()
            prr.save()
        # Debe haberse asignado un short_code por la ruta de fallback
        assert prr.short_code
        assert len(prr.short_code) == 8
        # No comprobamos unicidad real; sólo que se cubrió el camino de asignación de fallback
