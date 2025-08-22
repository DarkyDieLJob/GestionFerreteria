import os
import io
import tempfile
import pytest
from django.urls import reverse
from django.core.management import call_command
from django.apps import apps

pytest.importorskip("pandas", reason="multi-sheet flow usa pandas; se puede mockear si no está")


@pytest.fixture
@pytest.mark.django_db  # usar base por defecto
def proveedor_y_configs():
    Proveedor = apps.get_model("proveedores", "Proveedor")
    ConfigImportacion = apps.get_model("importaciones", "ConfigImportacion")

    prov = Proveedor.objects.create(
        nombre="Prov Multi",
        abreviatura="PM",
        descuento_comercial=0.0,
        margen_ganancia=1.5,
        margen_ganancia_efectivo=0.9,
        margen_ganancia_bulto=0.95,
    )
    cfg1 = ConfigImportacion.objects.create(
        proveedor=prov,
        nombre_config="default",
        col_codigo="A",
        col_descripcion="B",
        col_precio="C",
        instructivo="Instrucciones test",
    )
    cfg2 = ConfigImportacion.objects.create(
        proveedor=prov,
        nombre_config="alt",
        col_codigo=0,
        col_descripcion=1,
        col_precio=2,
    )
    return prov, cfg1, cfg2


@pytest.mark.django_db
def test_repository_generar_csvs_por_hoja_crea_pendientes(monkeypatch, tmp_path, proveedor_y_configs):
    prov, cfg1, cfg2 = proveedor_y_configs

    # Simular archivo subido en storage
    from django.core.files.storage import FileSystemStorage
    storage = FileSystemStorage()
    excel_path = tmp_path / "multi.xlsx"
    excel_path.write_bytes(b"fake-xlsx")

    saved_name = storage.save(excel_path.name, io.BytesIO(excel_path.read_bytes()))

    # Mock pandas.ExcelFile y conversion.convertir_a_csv
    import importaciones.adapters.repository as repo_mod

    class FakeXls:
        sheet_names = ["Hoja1", "Hoja2"]

    monkeypatch.setattr(repo_mod.pd, "ExcelFile", lambda *_a, **_k: FakeXls(), raising=True)

    out1 = str(tmp_path / "Prov_Hoja1.csv")
    out2 = str(tmp_path / "Prov_Hoja2.csv")
    monkeypatch.setattr(repo_mod, "convertir_a_csv", lambda *_a, **_k: [out1, out2], raising=True)

    from importaciones.adapters.repository import ExcelRepository

    repo = ExcelRepository()
    creados = repo.generar_csvs_por_hoja(
        proveedor_id=prov.pk,
        nombre_archivo=saved_name,
        selecciones={
            "Hoja1": {"config_id": cfg1.pk, "start_row": 1},
            "Hoja2": {"config_id": cfg2.pk, "start_row": 0},
        },
    )
    assert len(creados) == 2

    ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")
    qs = ArchivoPendiente.objects.filter(proveedor=prov, procesado=False)
    assert qs.count() == 2
    hojas = {ap.hoja_origen for ap in qs}
    assert hojas == {"Hoja1", "Hoja2"}


@pytest.mark.django_db
def test_command_procesar_pendientes_script_monkeypatched(monkeypatch, tmp_path, proveedor_y_configs):
    prov, cfg1, _ = proveedor_y_configs
    ArchivoPendiente = apps.get_model("importaciones", "ArchivoPendiente")

    # Crear CSV temporal y pendiente
    csv_path = tmp_path / "pend.csv"
    csv_path.write_text("codigo,descripcion,precio\n1,Prod,100\n")

    ap = ArchivoPendiente.objects.create(
        proveedor=prov,
        ruta_csv=str(csv_path),
        hoja_origen="Hoja1",
        config_usada=cfg1,
    )

    # Mock importar_csv para no tocar modelos de precios
    import importaciones.services.importador_csv as svc

    def fake_importar_csv(**kwargs):
        class Stats:
            filas_leidas = 1
            filas_validas = 1
            filas_descartadas = 0
        return Stats()

    monkeypatch.setattr(svc, "importar_csv", lambda *a, **k: fake_importar_csv(), raising=True)

    # Ejecutar comando
    call_command("procesar_pendientes_script", verbosity=0)

    # Verificar procesado y borrado de archivo
    ap.refresh_from_db()
    assert ap.procesado is True
    assert not os.path.exists(str(csv_path))


@pytest.mark.django_db  # vistas: GET y POST formset
def test_preview_get_and_post_formset_flow(client, monkeypatch, proveedor_y_configs):
    prov, cfg1, cfg2 = proveedor_y_configs

    # Mock listar_hojas del use case
    from importaciones.adapters.repository import ExcelRepository
    from importaciones.domain.use_cases import ImportarExcelUseCase

    monkeypatch.setattr(ExcelRepository, "listar_hojas_excel", lambda self, nombre: ["Hoja1", "Hoja2"], raising=True)
    # Mock generar_csvs_por_hoja para no crear archivos reales
    called = {"selecciones": None}

    def fake_gen(self, proveedor_id, nombre_archivo, selecciones):
        called["selecciones"] = selecciones
        return [("Hoja1", "/tmp/x1.csv"), ("Hoja2", "/tmp/x2.csv")]

    monkeypatch.setattr(ExcelRepository, "generar_csvs_por_hoja", fake_gen, raising=True)

    # GET debe renderizar un formset con 2 formularios
    url = reverse("importaciones:importacion_preview", kwargs={"proveedor_id": prov.pk, "nombre_archivo": "file.xlsx"})
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"name=\"form-0-hoja\"" in resp.content
    assert b"name=\"form-1-hoja\"" in resp.content

    # POST seleccionar solo Hoja1
    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-hoja": "Hoja1",
        "form-0-cargar": "on",
        "form-0-config": str(cfg1.pk),
        "form-0-start_row": "2",
        "form-1-hoja": "Hoja2",
        "form-1-cargar": "",  # no cargar
        "form-1-config": "",
        "form-1-start_row": "0",
    }
    resp2 = client.post(url, data=data)
    # Debe redirigir a confirmación
    assert resp2.status_code in (301, 302)
    assert called["selecciones"] == {"Hoja1": {"config_id": cfg1.pk, "start_row": 2}}


@pytest.mark.django_db  # integración mínima del landing -> preview
def test_landing_post_redirects_to_preview(client, monkeypatch, tmp_path, proveedor_y_configs, settings):
    prov, *_ = proveedor_y_configs

    # Preparar storage temporal
    media_dir = tmp_path / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(media_dir)

    # Mock listar_hojas para que preview funcione cuando redirija
    from importaciones.adapters.repository import ExcelRepository
    monkeypatch.setattr(ExcelRepository, "listar_hojas_excel", lambda self, nombre: ["Hoja1"], raising=True)

    # Archivo simulado subido
    file_content = io.BytesIO(b"fake-excel-content")
    file_content.name = "test.xlsx"

    url = reverse("importaciones:landing")
    resp = client.post(url, data={"proveedor_id": str(prov.pk), "archivo": file_content})
    assert resp.status_code in (301, 302)

    # La URL destino debe ser preview con el nombre del archivo guardado
    loc = resp.headers.get("Location", "")
    assert "/importaciones/preview/" in loc or "importacion_preview" in loc
