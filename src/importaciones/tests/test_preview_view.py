import json
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from django.test import Client

# Allow DB access to both 'default' and 'negocio_db' for these tests
pytestmark = pytest.mark.django_db(databases=["default", "negocio_db"], transaction=True)


def test_get_preview_renders_sections(client: Client):
    proveedor_id = 123
    nombre_archivo = "archivo.xlsx"
    url = reverse("importaciones:importacion_preview", kwargs={
        "proveedor_id": proveedor_id,
        "nombre_archivo": nombre_archivo,
    })

    # Mocks
    mock_use_case = MagicMock()
    mock_use_case.listar_hojas.return_value = ["Hoja1", "Hoja2"]
    mock_use_case.get_preview_for_sheet.side_effect = [
        {"columnas": ["A", "B"], "filas": [{"A": 1, "B": 2}], "total_filas": 1},
        {"columnas": ["X"], "filas": [{"X": "v"}], "total_filas": 1},
    ]

    class _DummyProveedor:
        def __init__(self, pk):
            self.id = pk
            self.pk = pk
            self.nombre = "Proveedor X"
        def __getitem__(self, key):
            if key in ("id", "pk"):
                return self.pk
            raise KeyError(key)

    dummy_proveedor_obj = _DummyProveedor(proveedor_id)

    with patch("importaciones.adapters.views.ImportarExcelUseCase", return_value=mock_use_case), \
         patch("importaciones.adapters.views.ExcelRepository"), \
         patch("importaciones.adapters.views.apps") as mock_apps:
        # Instructivos via apps.get_model(...)
        mock_cfg_model = MagicMock()
        mock_cfg_qs = MagicMock()
        mock_cfg_qs.filter.return_value.values_list.return_value = []
        mock_cfg_model.objects = mock_cfg_qs
        mock_apps.get_model.return_value = mock_cfg_model

        resp = client.get(url)

    assert resp.status_code == 200
    html = resp.content.decode()
    # Should render per-sheet headers and preview table headers
    assert "Hoja: Hoja1" in html
    assert "Hoja: Hoja2" in html
    assert ">A<" in html or "A</th>" in html
    assert ">B<" in html or "B</th>" in html
    # Should include config selection and cargar checkbox
    assert "config_choice" in html
    assert "cargar" in html


def test_post_creates_and_generates(client: Client):
    proveedor_id = 456
    nombre_archivo = "listado.xlsx"
    url = reverse("importaciones:importacion_preview", kwargs={
        "proveedor_id": proveedor_id,
        "nombre_archivo": nombre_archivo,
    })

    # Arrange GET behavior to obtain initial formset size
    mock_use_case = MagicMock()
    mock_use_case.listar_hojas.return_value = ["HojaA", "HojaB"]
    mock_use_case.get_preview_for_sheet.side_effect = [
        {"columnas": ["C1"], "filas": [{"C1": 10}], "total_filas": 1},
        {"columnas": ["C2"], "filas": [{"C2": 20}], "total_filas": 1},
    ]

    class _DummyProveedor:
        def __init__(self, pk):
            self.id = pk
            self.pk = pk
            self.nombre = "Proveedor Y"
        def __getitem__(self, key):
            if key in ("id", "pk"):
                return self.pk
            raise KeyError(key)

    dummy_proveedor_obj = _DummyProveedor(proveedor_id)

    with patch("importaciones.adapters.views.ImportarExcelUseCase", return_value=mock_use_case), \
         patch("importaciones.adapters.views.ExcelRepository") as MockRepo, \
         patch("importaciones.adapters.views.Proveedor") as MockProveedor, \
         patch("importaciones.adapters.views.apps") as mock_apps:
        # Proveedor and instructivos mocks
        MockProveedor.objects.get.return_value = dummy_proveedor_obj
        MockProveedor.objects.using.return_value.get.return_value = dummy_proveedor_obj
        mock_cfg_model = MagicMock()
        mock_cfg_qs = MagicMock()
        mock_cfg_qs.filter.return_value.values_list.return_value = []
        mock_cfg_model.objects = mock_cfg_qs
        mock_cfg_model.objects.using.return_value = mock_cfg_qs
        mock_apps.get_model.return_value = mock_cfg_model

        # initial GET to get management form structure
        resp_get = client.get(url)
        assert resp_get.status_code == 200

    # Prepare POST payload
    # We'll select HojaA with existing config id '1', and HojaB with new config created (returns pk 99)
    def _ensure_config_side_effect(**kwargs):
        obj = MagicMock()
        obj.pk = 99
        return obj

    with patch("importaciones.adapters.views.ImportarExcelUseCase", return_value=mock_use_case) as PatchedUC, \
         patch("importaciones.adapters.views.ExcelRepository") as MockRepo, \
         patch("importaciones.adapters.views.Proveedor") as MockProveedor, \
         patch("importaciones.adapters.views.apps") as mock_apps:
        mock_cfg_model = MagicMock()
        mock_cfg_qs = MagicMock()
        mock_cfg_qs.filter.return_value.values_list.return_value = []
        mock_cfg_model.objects = mock_cfg_qs
        mock_apps.get_model.return_value = mock_cfg_model
        MockProveedor.objects.get.return_value = dummy_proveedor_obj
        MockProveedor.objects.using.return_value.get.return_value = dummy_proveedor_obj

        repo_instance = MockRepo.return_value
        repo_instance.ensure_config.side_effect = _ensure_config_side_effect

        post_data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            # form 0 -> HojaA: cargar, existing config '1'
            "form-0-hoja": "HojaA",
            "form-0-cargar": "on",
            "form-0-start_row": "0",
            "form-0-config_choice": "1",
            # form 1 -> HojaB: cargar, new config with fields
            "form-1-hoja": "HojaB",
            "form-1-cargar": "on",
            "form-1-start_row": "2",
            "form-1-config_choice": "new",
            "form-1-nombre_config": "Cfg HOJAB",
            "form-1-col_codigo": "COD",
            "form-1-col_descripcion": "DESC",
            "form-1-col_precio": "PRECIO",
            "form-1-col_cant": "CANT",
            "form-1-col_iva": "IVA",
            "form-1-col_cod_barras": "BAR",
            "form-1-col_marca": "MARCA",
            "form-1-instructivo": "Usar desde fila 3",
        }

        resp_post = client.post(url, data=post_data, follow=False)

        # Should redirect to confirmation view
        assert resp_post.status_code in (301, 302)
        # And generar_csvs_por_hoja should have been called with selections mapping
        assert PatchedUC.return_value.generar_csvs_por_hoja.called
        args, kwargs = PatchedUC.return_value.generar_csvs_por_hoja.call_args
        # kwargs should include selecciones with config ids 1 and 99
        selecciones = kwargs.get("selecciones") or (args[2] if len(args) > 2 else {})
        assert "HojaA" in selecciones and selecciones["HojaA"]["config_id"] == 1
        assert "HojaB" in selecciones and selecciones["HojaB"]["config_id"] == 99
