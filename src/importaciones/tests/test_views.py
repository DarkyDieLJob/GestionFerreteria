import io
import os
import pytest
import pytest_django  # noqa: F401  # aseguramos disponibilidad de marcadores/fixtures
from django.urls import reverse
from django.core.files.uploadedfile import TemporaryUploadedFile
from importaciones.adapters.models import ConfigImportacion
from proveedores.models import Proveedor

# Evitar depender de archivos reales de Excel en estas pruebas
pytest.importorskip("pandas", reason="Se requieren dependencias de importaciones (pandas) para estas pruebas")


@pytest.fixture
@pytest.mark.django_db(databases=["negocio_db"])  # usamos la base de negocio
def proveedor_config():
    """Crea un Proveedor y su ConfigImportacion en la base negocio_db."""
    proveedor = Proveedor.objects.using("negocio_db").create(
        nombre="Proveedor Test",
        abreviatura="PT",
        descuento_comercial=0.0,
        margen_ganancia=1.5,
        margen_ganancia_efectivo=0.90,
        margen_ganancia_bulto=0.95,
    )
    ConfigImportacion.objects.using("negocio_db").create(
        proveedor=proveedor,
        col_codigo="A",
        col_descripcion="B",
        col_precio="C",
        col_cant="D",
        col_iva="E",
    )
    return proveedor


@pytest.mark.django_db(databases=["negocio_db"])  # nueva vista: landing GET
def test_landing_get_lists_proveedores_and_pendientes(client, proveedor_config, monkeypatch):
    url = reverse("importaciones:landing")
    resp = client.get(url)
    assert resp.status_code == 200
    # Debe listar proveedores en select
    assert b"proveedor_id" in resp.content


@pytest.mark.django_db(databases=["negocio_db"])  # landing POST redirige a preview
def test_landing_post_redirects_to_preview_min(client, monkeypatch, tmp_path, settings, proveedor_config):
    # Mock listar_hojas para que preview funcione tras redirigir
    from importaciones.adapters.repository import ExcelRepository
    monkeypatch.setattr(ExcelRepository, "listar_hojas_excel", lambda self, nombre: ["Hoja1"], raising=True)

    media_dir = tmp_path / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(media_dir)

    content = io.BytesIO(b"fake-excel")
    content.name = "test.xlsx"

    url = reverse("importaciones:landing")
    resp = client.post(url, data={"proveedor_id": str(proveedor_config.id), "archivo": content})
    assert resp.status_code in (301, 302)


@pytest.mark.django_db(databases=["negocio_db"])  # preview GET basado en hojas
def test_importacion_preview_get_lists_sheets(client, monkeypatch, proveedor_config):
    from importaciones.adapters.repository import ExcelRepository
    monkeypatch.setattr(ExcelRepository, "listar_hojas_excel", lambda self, nombre: ["H1", "H2"], raising=True)

    url = reverse(
        "importaciones:importacion_preview",
        kwargs={"proveedor_id": proveedor_config.id, "nombre_archivo": "test.xlsx"},
    )
    resp = client.get(url)
    assert resp.status_code == 200
    # Debe renderizar formset de hojas
    assert b"form-0-hoja" in resp.content and b"form-1-hoja" in resp.content
