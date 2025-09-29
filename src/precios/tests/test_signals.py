import types
from types import SimpleNamespace
from decimal import Decimal

import pytest
from unittest.mock import MagicMock, patch

from precios import signals


def test_post_migrate_ignores_non_precios_sender():
    sender = SimpleNamespace(name="otra_app")
    # Should be a no-op: just ensure it doesn't crash and doesn't call apps.get_model
    with patch.object(signals.apps, "get_model") as gm:
        signals.create_default_descuento(sender)
        gm.assert_not_called()


def test_post_migrate_creates_default_descuento_on_negocio_db():
    sender = SimpleNamespace(name="precios")
    fake_model = MagicMock()
    with patch.object(signals.apps, "get_model", return_value=fake_model) as gm:
        signals.create_default_descuento(sender)
        gm.assert_called_once_with("precios", "Descuento")
        fake_model.objects.using.assert_called_once_with("negocio_db")
        args, kwargs = fake_model.objects.using.return_value.get_or_create.call_args
        assert kwargs["defaults"]["efectivo"] == Decimal("0.10")
        assert kwargs["defaults"]["bulto"] == Decimal("0.05")
        assert kwargs["defaults"]["cantidad_bulto"] == 5
        assert kwargs["defaults"]["general"] == Decimal("0.0")
        assert kwargs["defaults"]["temporal"] is False
