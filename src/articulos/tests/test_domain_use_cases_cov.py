import pytest

from articulos.domain.use_cases import (
    CalcularPrecioUseCase,
    BuscarArticuloUseCase,
    MapearArticuloUseCase,
)


class _PrecioRepoStub:
    def __init__(self, result=None):
        self.calls = []
        self.result = result if result is not None else {
            "base": 10.0,
            "final": 12.0,
            "final_efectivo": 11.0,
            "bulto": 9.0,
            "final_bulto": 10.0,
            "final_bulto_efectivo": 9.5,
        }

    def calcular_precios(self, articulo_id, tipo, cantidad, pago_efectivo):
        self.calls.append({
            "articulo_id": articulo_id,
            "tipo": tipo,
            "cantidad": cantidad,
            "pago_efectivo": pago_efectivo,
        })
        return self.result


class _BusquedaRepoStub:
    def __init__(self, result=None):
        self.calls = []
        self.result = result

    def buscar_articulos(self, query, abreviatura=None):
        self.calls.append({"query": query, "abreviatura": abreviatura})
        return self.result


class _MapeoRepoStub:
    def __init__(self, result=None):
        self.calls = []
        self.result = result if result is not None else {"status": "ok", "rel": True}

    def mapear_articulo(self, articulo_s_revisar_id, articulo_id, usuario_id):
        self.calls.append({
            "articulo_s_revisar_id": articulo_s_revisar_id,
            "articulo_id": articulo_id,
            "usuario_id": usuario_id,
        })
        return self.result


def test_calcular_precio_use_case_valid_flow_and_normalization():
    repo = _PrecioRepoStub()
    uc = CalcularPrecioUseCase(repo)

    # cantidad inválida -> se normaliza a 1
    out = uc.execute(articulo_id=123, tipo="  articulo ", cantidad=0, pago_efectivo=True)

    assert out["final"] == 12.0
    assert repo.calls and repo.calls[-1]["cantidad"] == 1
    # tipo es strip()
    assert repo.calls[-1]["tipo"] == "articulo"


def test_calcular_precio_use_case_validations():
    uc = CalcularPrecioUseCase(_PrecioRepoStub())

    with pytest.raises(ValueError):
        uc.execute(articulo_id=None, tipo="articulo")
    with pytest.raises(ValueError):
        uc.execute(articulo_id=1, tipo="   ")

    # cantidad no entera -> cae en except y normaliza a 1
    out = uc.execute(articulo_id=1, tipo="articulo", cantidad="x")
    assert out["base"] == 10.0


def test_calcular_precio_use_case_empty_repo_result():
    uc = CalcularPrecioUseCase(_PrecioRepoStub(result={}))
    out = uc.execute(articulo_id=1, tipo="articulo", cantidad=2)
    # retorna estructura vacía si repo None/{}
    assert out == {}


def test_buscar_articulo_use_case_no_input_returns_empty_list():
    uc = BuscarArticuloUseCase(_BusquedaRepoStub(result=[{"id": 1}]))
    assert uc.execute(query="  ", abreviatura=None) == []


def test_buscar_articulo_use_case_delegates_and_fallback_list():
    uc = BuscarArticuloUseCase(_BusquedaRepoStub(result=None))
    out = uc.execute(query="37", abreviatura="vj")
    # sin resultados -> lista vacía
    assert out == []


def test_mapear_articulo_use_case_validations_and_delegation():
    repo = _MapeoRepoStub()
    uc = MapearArticuloUseCase(repo)

    with pytest.raises(ValueError):
        uc.execute(articulo_s_revisar_id=None, articulo_id=2, usuario_id=3)
    with pytest.raises(ValueError):
        uc.execute(articulo_s_revisar_id=1, articulo_id="", usuario_id=3)
    with pytest.raises(ValueError):
        uc.execute(articulo_s_revisar_id=1, articulo_id=2, usuario_id=None)

    out = uc.execute(articulo_s_revisar_id=1, articulo_id=2, usuario_id=3)
    assert out["status"] == "ok"
    assert repo.calls and repo.calls[-1]["articulo_id"] == 2
