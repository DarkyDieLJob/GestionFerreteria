from decimal import Decimal

import pytest

from articulos.domain import pricing


def test__to_dec_handles_exception_returns_zero():
    class Bad:
        def __str__(self):
            raise RuntimeError("boom")
    assert pricing._to_dec(Bad()) == Decimal("0")


def test_calculate_prices_dividir_true_with_bulto():
    # Minimal scenario focusing the dividir=True branch
    result = pricing.calculate_prices(
        precio_de_lista=100,
        iva=0,
        proveedor_desc_com=0,
        proveedor_margen=1,
        proveedor_margen_ef=1,
        descuento_general=0,
        descuento_activo=False,
        descuento_bulto=0,
        descuento_cantidad_bulto=None,
        bulto_articulo=5,
        cantidad=1,
        dividir=True,
    )
    # base debe dividir lista por bulto (100/5 = 20)
    assert result["base"] == Decimal("20.00")
    assert result["final"] == Decimal("20.00")
    # bulto = base * bulto_qty (20 * 5)
    assert result["bulto"] == Decimal("100.00")
