from core_app.adapters.models import Core_app


def test_core_app_str_returns_name():
    # No tocar la base de datos: solo validar __str__
    item = Core_app(name="Item A")
    assert str(item) == "Item A"
