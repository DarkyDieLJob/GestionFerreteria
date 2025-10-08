import io
import os
import pytest
import pytest_django  # noqa: F401  # aseguramos disponibilidad de marcadores/fixtures
from django.urls import reverse
from django.core.files.uploadedfile import TemporaryUploadedFile
from importaciones.adapters.models import ConfigImportacion
from proveedores.models import Proveedor

# Si alguna ruta importara pandas indirectamente, evitamos fallar en recolección
pytest.importorskip("pandas", reason="Se requieren dependencias de importaciones (pandas) para estas pruebas")


@pytest.fixture
@pytest.mark.django_db
def proveedor_config():
    """Crea un Proveedor y su ConfigImportacion en la base por defecto."""
    proveedor = Proveedor.objects.create(
        nombre="Proveedor Test",
        abreviatura="PT",
        descuento_comercial=0.0,
        margen_ganancia=1.5,
        margen_ganancia_efectivo=0.90,
        margen_ganancia_bulto=0.95,
    )
    ConfigImportacion.objects.create(
        proveedor=proveedor,
        col_codigo="A",
        col_descripcion="B",
        col_precio="C",
        col_cant="D",
        col_iva="E",
    )
    return proveedor


@pytest.mark.django_db
def test_importacion_create_get(client, proveedor_config):
    url = reverse("importaciones:importacion_create", kwargs={"proveedor_id": proveedor_config.id})
    resp = client.get(url)
    assert resp.status_code == 200
    # Debe renderizar el formulario (campo 'archivo')
    assert b"type=\"file\"" in resp.content or b"Archivo Excel" in resp.content


@pytest.mark.django_db
def test_importacion_create_post(client, monkeypatch, tmp_path, settings, proveedor_config):
    # Redirigirá al listado de proveedores tras procesar
    called = {"args": None}

    def fake_procesar_excel(self, proveedor_id, nombre_archivo):
        called["args"] = (proveedor_id, nombre_archivo)
        # Simular procesamiento sin efectos
        return None

    # Parchear el repositorio
    from importaciones.adapters.repository import ExcelRepository

    monkeypatch.setattr(ExcelRepository, "procesar_excel", fake_procesar_excel, raising=True)

    # Asegurar un MEDIA_ROOT temporal para no ensuciar el entorno
    media_dir = tmp_path / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(media_dir)

    # Crear archivo subido temporal
    content = b"codigo,descripcion,precio,iva,cant\n1,Prod,100,0.21,1\n"
    # TemporaryUploadedFile(name, content_type, size, charset)
    tmp_upload = TemporaryUploadedFile(
        name="test.csv", content_type="text/csv", size=len(content), charset="utf-8"
    )
    tmp_upload.write(content)
    tmp_upload.seek(0)

    url = reverse("importaciones:importacion_create", kwargs={"proveedor_id": proveedor_config.id})
    resp = client.post(url, data={"archivo": tmp_upload})

    # Debe redirigir al listado de proveedores
    assert resp.status_code in (301, 302)
    assert called["args"] is not None
    assert called["args"][0] == proveedor_config.id
    # El nombre_archivo será el nombre asignado por el storage
    assert isinstance(called["args"][1], str) and called["args"][1]


@pytest.mark.django_db
def test_importacion_preview_get(client, monkeypatch, proveedor_config):
    # Parchear vista_previa_excel para devolver filas controladas
    preview_rows = [
        {"codigo": "1", "descripcion": "P1", "precio": "100", "iva": "0.21", "cant": "1"},
        {"codigo": "2", "descripcion": "P2", "precio": "200", "iva": "0.21", "cant": "1"},
    ]

    from importaciones.adapters.repository import ExcelRepository

    monkeypatch.setattr(
        ExcelRepository,
        "vista_previa_excel",
        lambda self, proveedor_id, nombre_archivo, limite=20: preview_rows,
        raising=True,
    )

    url = reverse(
        "importaciones:importacion_preview",
        kwargs={"proveedor_id": proveedor_config.id, "nombre_archivo": "test.csv"},
    )
    resp = client.get(url)
    assert resp.status_code == 200

    # Validar que el contexto contenga las filas esperadas
    assert "filas" in resp.context
    assert resp.context["filas"] == preview_rows
    # Y que parte del contenido renderizado incluya un código
    assert b">1<" in resp.content or b"P1" in resp.content
