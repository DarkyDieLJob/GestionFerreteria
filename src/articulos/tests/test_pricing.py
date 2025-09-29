import pytest
from decimal import Decimal

from articulos.domain.pricing import (
    _normalize_factor_or_percent,
    round_money,
    calculate_prices,
)


def test_round_money_half_up_basic():
    assert round_money(Decimal("1.005")) == Decimal("1.01")
    assert round_money(Decimal("1.004")) == Decimal("1.00")


@pytest.mark.parametrize(
    "val,expected",
    [
        (0, Decimal("0")),
        (1, Decimal("0")),
        (5, Decimal("0.05")),
        (10, Decimal("0.10")),
        (100, Decimal("1")),
        (0.25, Decimal("0.25")),
        ("0.30", Decimal("0.30")),
        (-5, Decimal("0")),
    ],
)
def test_normalize_factor_or_percent(val, expected):
    assert _normalize_factor_or_percent(val) == expected


# Escenarios canónicos provistos:
# - PrecioDeLista.precio = 100
# - PrecioDeLista.bulto = 1 y 6
# - PrecioDeLista.iva = 12% y 10.5%
# - Descuentos:
#   nombre: "Sin Descuento", "Descuento x6" y "Descuento X10"
#   efectivo: 0.00, 0.1 y 0.1  -> se mapea a proveedor_margen_ef = 1 - efectivo
#   bulto:    0.00, 0.05 y 0.10 -> descuento sobre el total de bulto (porcentaje)
#   general:  0.00
#   temporal: False y True (afecta a descuento_general, aquí 0 => sin efecto)

@pytest.mark.parametrize(
    "iva,bulto_articulo,desc_nombre,efectivo_factor,desc_bulto_pct,temporal,expected",
    [
        # Sin Descuento, IVA 12%, bulto 1 y 6
        (Decimal("0.12"), 1, "Sin Descuento", Decimal("0.00"), Decimal("0.00"), False,
         {"final": Decimal("112.00"), "final_ef": Decimal("112.00"), "final_bulto": Decimal("112.00"), "final_bulto_ef": Decimal("112.00")} ),
        (Decimal("0.12"), 6, "Sin Descuento", Decimal("0.00"), Decimal("0.00"), False,
         {"final": Decimal("112.00"), "final_ef": Decimal("112.00"), "final_bulto": Decimal("672.00"), "final_bulto_ef": Decimal("672.00")} ),
        # Sin Descuento, IVA 10.5%, bulto 1 y 6
        (Decimal("0.105"), 1, "Sin Descuento", Decimal("0.00"), Decimal("0.00"), False,
         {"final": Decimal("110.50"), "final_ef": Decimal("110.50"), "final_bulto": Decimal("110.50"), "final_bulto_ef": Decimal("110.50")} ),
        (Decimal("0.105"), 6, "Sin Descuento", Decimal("0.00"), Decimal("0.00"), False,
         {"final": Decimal("110.50"), "final_ef": Decimal("110.50"), "final_bulto": Decimal("663.00"), "final_bulto_ef": Decimal("663.00")} ),

        # Descuento x6: efectivo 10% (margen_ef=0.9), bulto 5% (sobre total bulto), IVA 12% y 10.5%
        (Decimal("0.12"), 6, "Descuento x6", Decimal("0.10"), Decimal("0.05"), False,
         {"final": Decimal("112.00"), "final_ef": Decimal("100.80"), "final_bulto": Decimal("638.40"), "final_bulto_ef": Decimal("574.56")} ),
        (Decimal("0.105"), 6, "Descuento x6", Decimal("0.10"), Decimal("0.05"), True,
         {"final": Decimal("110.50"), "final_ef": Decimal("99.45"), "final_bulto": Decimal("629.85"), "final_bulto_ef": Decimal("566.87")} ),

        # Descuento X10: efectivo 10%, bulto 10%
        (Decimal("0.12"), 6, "Descuento X10", Decimal("0.10"), Decimal("0.10"), False,
         {"final": Decimal("112.00"), "final_ef": Decimal("100.80"), "final_bulto": Decimal("604.80"), "final_bulto_ef": Decimal("544.32")} ),
        (Decimal("0.105"), 6, "Descuento X10", Decimal("0.10"), Decimal("0.10"), True,
         {"final": Decimal("110.50"), "final_ef": Decimal("99.45"), "final_bulto": Decimal("596.70"), "final_bulto_ef": Decimal("537.03")} ),
    ],
)
def test_pricing_casos_canonicos(iva, bulto_articulo, desc_nombre, efectivo_factor, desc_bulto_pct, temporal, expected):
    precio_de_lista = 100
    proveedor_desc_com = 0
    proveedor_margen = 1.0
    proveedor_margen_ef = Decimal("1.00") - Decimal(efectivo_factor)
    descuento_general = 0  # explícito, no aplica
    descuento_activo = bool(temporal)
    dividir = False

    result = calculate_prices(
        precio_de_lista=precio_de_lista,
        iva=iva,
        proveedor_desc_com=proveedor_desc_com,
        proveedor_margen=proveedor_margen,
        proveedor_margen_ef=proveedor_margen_ef,
        descuento_general=descuento_general,
        descuento_activo=descuento_activo,
        descuento_bulto=(desc_bulto_pct * 100),  # API espera porcentaje
        descuento_cantidad_bulto=None,  # aplica siempre a totales de bulto
        bulto_articulo=bulto_articulo,
        cantidad=1,
        dividir=dividir,
    )

    assert result["final"] == expected["final"], f"{desc_nombre} (iva={iva}, bulto={bulto_articulo})"
    assert result["final_efectivo"] == expected["final_ef"], f"{desc_nombre} (iva={iva}, bulto={bulto_articulo})"
    assert result["final_bulto"] == expected["final_bulto"], f"{desc_nombre} (iva={iva}, bulto={bulto_articulo})"
    assert result["final_bulto_efectivo"] == expected["final_bulto_ef"], f"{desc_nombre} (iva={iva}, bulto={bulto_articulo})"


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
