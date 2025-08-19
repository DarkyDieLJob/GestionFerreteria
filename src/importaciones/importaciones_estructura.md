# Informe de la aplicación “importaciones” (src/importaciones)

## 1) Propósito general
- La app “importaciones” implementa un flujo para:
  - Seleccionar un proveedor.
  - Subir un archivo de lista de precios (Excel/CSV/ODS).
  - Previsualizar las primeras filas del archivo.
  - Procesar el archivo para crear/actualizar precios de lista y generar artículos sin revisar.
- Arquitectura hexagonal: las vistas/adapters delegan al repositorio y a los casos de uso del dominio; los servicios encapsulan operaciones técnicas (conversión/parseo).

## 2) Estructura de directorios y archivos principales
```
src/importaciones/
├─ adapters/
│  ├─ forms.py                 # Formulario de subida de archivo con validación de extensiones
│  ├─ models.py                # Modelo ConfigImportacion (mapeos por proveedor)
│  ├─ repository.py            # ExcelRepository (implementa puerto del dominio)
│  ├─ serializers.py           # Placeholder mínimo
│  ├─ urls.py                  # (Opcional) urls del submódulo adapters
│  └─ views.py                 # Vistas Django (landing, create, preview)
├─ domain/
│  └─ use_cases.py             # ImportarExcelPort (puerto) e ImportarExcelUseCase
├─ ports/
│  └─ interfaces.py            # Marcador para interfaces del dominio
├─ services/
│  ├─ conversion.py            # Conversión de xls/xlsx/ods a CSV (pandas)
│  └─ importador_csv.py        # Importación desde CSV con métricas y upsert
├─ templates/
│  ├─ base.html
│  └─ auth/
│     ├─ login.html
│     └─ register.html
├─ migrations/                 # Incluye 0001_initial.py
├─ tests/                      # Suite de pruebas (adapters, services, vistas, integración)
├─ urls.py                     # Endpoints públicos de la app (landing, create, preview)
├─ apps.py                     # Configuración Django de la app
├─ config.py                   # Configuración auxiliar
└─ procesar_excel_script.py    # Script utilitario para procesamiento
```

## 3) Vistas y flujo (importaciones/urls.py y adapters/views.py)
- Namespace: `app_name = "importaciones"`.
- Rutas:
  - `""` → `ImportacionesLandingView.as_view()`, name="landing".
  - `"crear/<int:proveedor_id>/"` → `ImportacionCreateView.as_view()`, name="importacion_create".
  - `"vista-previa/<int:proveedor_id>/<str:nombre_archivo>/"` → `ImportacionPreviewView.as_view()`, name="importacion_preview".

- Comportamiento de las vistas:
  - `ImportacionesLandingView` (GET/POST):
    - GET: lista proveedores desde `negocio_db` y renderiza `importaciones/landing.html`.
    - POST: exige `proveedor_id`; si falta, vuelve a mostrar el selector con mensaje; si está, redirige a `importacion_create`.
  - `ImportacionCreateView` (FormView):
    - Usa `ImportacionForm` (FileField) y `FileSystemStorage` para guardar el archivo en `MEDIA_ROOT`.
    - Llama a `ExcelRepository.procesar_excel(proveedor_id, nombre_archivo)`.
    - Redirige a `reverse("proveedores:proveedor_list")` al finalizar.
  - `ImportacionPreviewView` (GET):
    - Obtiene proveedor y archivo de la URL.
    - Llama a `ExcelRepository.vista_previa_excel(..., limite=20)` y renderiza `importaciones/importacion_preview.html`.

## 4) Dominio y repositorio
- `domain/use_cases.py`:
  - `ImportarExcelPort`: interfaz con `procesar_excel()` y `vista_previa_excel()`.
  - `ImportarExcelUseCase`: clase que delega en el puerto; Python puro sin dependencias de Django.

- `adapters/repository.py` (ExcelRepository):
  - Implementa `ImportarExcelPort` usando `pandas`, `FileSystemStorage` y Django ORM.
  - Opera siempre sobre la BD `negocio_db` y en transacciones atómicas (`transaction.atomic(using="negocio_db")`).
  - `vista_previa_excel(...)`: lee el archivo con pandas, devuelve columnas, primeras 20 filas y metadatos.
  - `procesar_excel(...)`:
    - Carga dinámicamente modelos: `Proveedor`, `ConfigImportacion`, `PrecioDeLista`, `ArticuloSinRevisar`, `Descuento`.
    - Obtiene `ConfigImportacion` para mapear columnas (código/descripcion/precio) y valida existencia.
    - Normaliza datos (strip, conversión de precio a numérico) y arma lotes.
    - Inserta con `bulk_create` (batch_size=1000, `ignore_conflicts=True`) en `PrecioDeLista` y `ArticuloSinRevisar`.
    - Elimina el archivo al finalizar.

## 5) Formularios y modelos del adaptador
- `adapters/forms.py` → `ImportacionForm`:
  - `FileField` con validación de extensiones permitidas: `.xlsx`, `.xls`, `.ods`, `.csv`.
- `adapters/models.py` → `ConfigImportacion`:
  - FK a `proveedores.Proveedor`.
  - Campos para mapeos de columnas (código, descripción, precio, cantidad, IVA, código de barras, marca).
  - `unique_together` por proveedor.

## 6) Servicios
- `services/conversion.py` → `convertir_a_csv(input_path, ...)`:
  - Convierte xls/xlsx/ods a CSV mediante pandas (lectura `header=None`).
  - Engines: `openpyxl` (xlsx), `xlrd` (xls), `odf` (ods).
  - Devuelve la ruta del CSV; si el input ya es `.csv`, retorna el mismo path.
- `services/importador_csv.py`:
  - `ImportStats` (dataclass) con métricas de procesamiento.
  - `leer_csv_en_filas(...)`: generador para iterar a partir de una fila inicial.
  - `importar_csv(...)`:
    - Valida cada fila; convierte precio a `Decimal`.
    - Upsert de `PrecioDeLista` por `(proveedor, codigo)` y `get_or_create` de `ArticuloSinRevisar`.
    - Modo `dry_run` para no escribir y solo contabilizar.

## 7) Tests
- Cobertura de: vistas (`test_views.py`), importador CSV (unitario e integración), conversión (unitario y con archivos reales), adapters y casos de uso.
- `fixtures/` con archivos y datos de apoyo para pruebas.

## 8) Consideraciones de base de datos y enrutado
- Todas las operaciones de negocio apuntan a `negocio_db` (ORM con `.using("negocio_db")`).
- Transacciones atómicas durante el procesamiento para consistencia.
- `urls.py` de la app está listo para incluirse desde el enrutador principal.

## 9) Observaciones y recomendaciones
- Asegurar que las plantillas `importaciones/*.html` existan en el árbol global de templates del proyecto (esta app incluye `base.html` y `auth/*`, pero no las específicas que las vistas referencian).
- Verificar dependencias de pandas y engines (`openpyxl`, `xlrd`, `odfpy`) cuando se use conversión.
- Mantener alineados los nombres de campos de `ConfigImportacion` con los usados por el repositorio (mapeos de columnas).
- Confirmar que el destino de redirección `proveedores:proveedor_list` esté disponible.
