import pytest
from decimal import Decimal

from articulos.domain.pricing import (
    _normalize_factor_or_percent,
    round_money,
    calculate_prices,
)


@pytest.mark.parametrize(
    "val,expected",
    [
        (0, Decimal("0")),
        (1, Decimal("0")),  # 1 como porcentaje => sin efecto según regla
        (5, Decimal("0.05")),
        (10, Decimal("0.10")),
        (100, Decimal("1")),
        (0.25, Decimal("0.25")),  # ya es factor
        ("0.30", Decimal("0.30")),
        (-5, Decimal("0")),
    ],
)
def test_normalize_factor_or_percent(val, expected):
    assert _normalize_factor_or_percent(val) == expected


def test_round_money_half_up():
    # 2 decimales, HALF_UP
    assert round_money(Decimal("1.005")) == Decimal("1.01")
    assert round_money(Decimal("1.004")) == Decimal("1.00")


@pytest.mark.parametrize(
    "params,expect",
    [
        # Caso base: sin descuentos, sin bulto
        (
            dict(
                precio_de_lista=100,
                iva=0.21,
                proveedor_desc_com=0,
                proveedor_margen=1.5,
                proveedor_margen_ef=0.9,
                descuento_general=0,
                descuento_activo=False,
                descuento_bulto=0,
                descuento_cantidad_bulto=None,
                bulto_articulo=1,
                cantidad=1,
                dividir=False,
            ),
            dict(
                base=Decimal("121.00"),
                final=Decimal("181.50"),
                final_efectivo=Decimal("163.35"),
                bulto=Decimal("121.00"),
                final_bulto=Decimal("181.50"),
                final_bulto_efectivo=Decimal("163.35"),
            ),
        ),
        # Bulto con descuento por bulto 10% aplicable sin umbral (None)
        (
            dict(
                precio_de_lista=200,
                iva=0.21,
                proveedor_desc_com=0.1,  # 10% desc comercial
                proveedor_margen=1.2,
                proveedor_margen_ef=0.85,
                descuento_general=0,
                descuento_activo=False,
                descuento_bulto=10,  # porcentaje
                descuento_cantidad_bulto=None,
                bulto_articulo=5,
                cantidad=1,
                dividir=False,
            ),
            None,  # validaremos relaciones, no exact match en todos
        ),
        # Descuento general activo como porcentaje (20) con umbral de bulto 3 alcanzado por cantidad
        (
            dict(
                precio_de_lista=50,
                iva=0.21,
                proveedor_desc_com=0,
                proveedor_margen=1.3,
                proveedor_margen_ef=1.0,
                descuento_general=20,  # porcentaje
                descuento_activo=True,
                descuento_bulto=5,  # porcentaje
                descuento_cantidad_bulto=3,
                bulto_articulo=2,
                cantidad=4,  # >= umbral
                dividir=False,
            ),
            None,
        ),
        # Dividir por bulto (precio unitario derivado del bulto)
        (
            dict(
                precio_de_lista=100,
                iva=0.21,
                proveedor_desc_com=0,
                proveedor_margen=1.1,
                proveedor_margen_ef=1.0,
                descuento_general=0,
                descuento_activo=False,
                descuento_bulto=0,
                descuento_cantidad_bulto=None,
                bulto_articulo=4,
                cantidad=1,
                dividir=True,
            ),
            None,
        ),
    ],
)
def test_calculate_prices_scenarios(params, expect):
    res = calculate_prices(**params)

    # Campos base siempre presentes
    for k in [
        "base",
        "final",
        "final_efectivo",
        "bulto",
        "final_bulto",
        "final_bulto_efectivo",
        "cantidad_bulto_aplicada",
        "cantidad_bulto_articulo",
        "umbral_descuento_bulto",
        "debug_descuento_bulto",
        "debug_factor_descuento_bulto",
        "debug_bulto_articulo",
        "debug_cantidad",
        "debug_cantidad_bulto_politica",
        "debug_aplica_descuento_bulto",
        "debug_min_qty",
        "debug_applied_qty",
    ]:
        assert k in res

    # Caso con expect exacto
    if expect is not None:
        for k, v in expect.items():
            assert res[k] == v

    # Invariantes y relaciones básicas
    assert res["base"] > 0
    assert res["final"] >= 0
    assert res["final_bulto"] >= 0

    # Si hay descuento_bulto > 0 y aplica, final_bulto debe ser <= final * bulto
    bulto = Decimal(str(params.get("bulto_articulo", 1)))
    final_unit = res["final"]
    nominal_bulto = (final_unit * bulto).quantize(Decimal("0.01"))

    if params.get("descuento_bulto", 0) and (
        (params.get("descuento_cantidad_bulto") in (None, 0, 1))
        or (Decimal(str(params.get("cantidad", 0))) >= Decimal(str(params.get("descuento_cantidad_bulto", 0))))
        or (bulto >= Decimal(str(params.get("descuento_cantidad_bulto", 0) or 0)))
    ):
        assert res["final_bulto"] <= nominal_bulto
    else:
        # sin descuento por bulto, debería ser igual al nominal
        assert res["final_bulto"] == nominal_bulto


@pytest.mark.parametrize(
    "descuento_activo,descuento_general,expected_rel",
    [
        (True, 0.2, "<="),  # 20% factor
        (True, 20, "<="),   # 20% porcentaje
        (False, 50, "=="),  # inactivo => no afecta
    ],
)
def test_descuento_general_factor_o_porcentaje(descuento_activo, descuento_general, expected_rel):
    base_params = dict(
        precio_de_lista=100,
        iva=0,
        proveedor_desc_com=0,
        proveedor_margen=1.0,
        proveedor_margen_ef=1.0,
        descuento_bulto=0,
        descuento_cantidad_bulto=None,
        bulto_articulo=1,
        cantidad=1,
        dividir=False,
    )
    res = calculate_prices(descuento_activo=descuento_activo, descuento_general=descuento_general, **base_params)

    # final con descuento activo no debe ser mayor que sin descuento
    res_sin = calculate_prices(descuento_activo=False, descuento_general=0, **base_params)

    if expected_rel == "<=":
        assert res["final"] <= res_sin["final"]
    else:
        assert res["final"] == res_sin["final"]
