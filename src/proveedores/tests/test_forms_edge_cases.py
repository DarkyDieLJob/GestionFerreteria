import pytest
from django.core.exceptions import ValidationError

from proveedores.adapters.forms import ProveedorForm

pytestmark = pytest.mark.django_db


def make_form(**data):
    # Minimal required fields for the form
    base = {
        "nombre": "Proveedor X",
        "abreviatura": data.get("abreviatura", "ABC"),
        "descuento_comercial": 0,
        "margen_ganancia": 1,
        "margen_ganancia_efectivo": 1,
        "margen_ganancia_bulto": 1,
    }
    return ProveedorForm(data=base)


def test_abreviatura_required():
    form = make_form(abreviatura="   ")
    assert not form.is_valid()
    assert "abreviatura" in form.errors
    # Basta con que haya al menos un error para el campo
    assert form.errors["abreviatura"], "Debe existir al menos un error en abreviatura"


def test_abreviatura_max_length():
    form = make_form(abreviatura="ABCD")
    assert not form.is_valid()
    assert "abreviatura" in form.errors
    assert any("máximo 3" in str(e).lower() for e in form.errors["abreviatura"])  # 3 caracteres


def test_abreviatura_only_letters_and_normalized():
    # Con números debe fallar
    form_bad = make_form(abreviatura="a1")
    assert not form_bad.is_valid()
    assert any("solo" in str(e).lower() for e in form_bad.errors["abreviatura"])  # solo letras

    # Con minúsculas válidas debe normalizar a mayúsculas y pasar
    form_ok = make_form(abreviatura="ab")
    assert form_ok.is_valid()
    assert form_ok.cleaned_data["abreviatura"] == "AB"
