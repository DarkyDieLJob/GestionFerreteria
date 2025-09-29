# Importaciones — Objetivos de Pruebas de Integración (Checklist)

Propósito: validar la interacción entre capas (vistas/adaptadores/repositorios/servicios), usando Django Test Client y/mocks parciales. Minimizar IO real salvo en fixtures controladas.

Flujo multi-hoja (vista previa y POST)
- [ ] GET /importaciones/preview renderiza secciones por hoja (headers/tabla) usando UseCase.listar_hojas y get_preview_for_sheet
  - Por qué: asegura que la UI muestre correctamente varias hojas y sus columnas/filas de ejemplo.
- [ ] GET incluye selección de configuración y checkbox "cargar" por hoja
  - Por qué: son controles críticos para decidir qué se procesa y cómo.
- [ ] POST con mezcla de config existente y nueva crea/asegura configs y llama UseCase.generar_csvs_por_hoja con `selecciones` correctas
  - Por qué: valida orquestación de creación/selección de config + mapping hoja -> (config_id, start_row).

Escenarios negativos en vista previa/POST
- [ ] Proveedor inexistente → respuesta apropiada (404 o mensaje) y NO se invoca UseCase
  - Por qué: robustez ante inputs inválidos y seguridad de información.
- [ ] Archivo sin hojas válidas → renderiza aviso; POST sin selecciones NO llama a generar_csvs
  - Por qué: evita ejecuciones nulas o errores silenciosos.
- [ ] Formset inválido (p. ej., start_row no numérico o < 0) → se muestran errores y no se procesa
  - Por qué: validación del lado servidor coherente con expectativas de UI.
- [ ] Fallo en ensure_config (excepción) → se maneja con mensaje/estado y NO se llama a generar_csvs
  - Por qué: evita efectos colaterales y facilita diagnóstico.

Repository/adapter de Excel
- [ ] ExcelRepository.ensure_config: cuando `config_choice == "new"` crea config con campos mínimos; cuando es id existente, no crea
  - Por qué: comportamiento idempotente y predecible.
- [ ] Generación de `selecciones` preserva start_row enteros y mapeos exactos
  - Por qué: la capa de servicios depende de la consistencia del payload.

Servicios y scripts
- [ ] importaciones.services.importador_csv: integración básica con csvs de fixtures (archivos chicos), validando conteos y mapeos
  - Por qué: asegura compatibilidad con datos reales sin depender de Excel.
- [ ] management command `procesar_pendientes_script`: con `call_command`, procesa pendientes mockeando `apps.get_model` e `importar_csv` y reporta métricas
  - Por qué: garantiza que la automatización por consola funcione y no rompa al cambiar modelos.
- [ ] Script `procesar_excel_script.py`: entrada de línea de comandos válida, errores por parámetros faltantes y happy path con mocks
  - Por qué: ayuda operativa y estabilidad de tooling externo al panel web.

Regresión/contratos
- [ ] Contrato UseCase-Adapter: cuando falta un método en el adaptador, el error es evidente y testeado en integración ligera
  - Por qué: cambios en signaturas o contratos deben detectarse tempranamente.

Notas:
- Usar `@pytest.mark.django_db` según corresponda.
- Evitar tocar `templates/app_templates/` u otros directorios excluidos de pruebas.
- Preferir mocks de borde (DB/IO) manteniendo lógica real en medio para mayor valor de integración.
