# Importaciones — Objetivos de Pruebas Unitarias (Checklist)

Propósito: asegurar la orquestación correcta del caso de uso y validar decisiones de dominio sin depender de Django ni de IO (Excel/DB). Cada ítem incluye el porqué/contexto para reducir ambigüedad.

- [ ] UseCase.procesar delega en el puerto con los argumentos correctos y retorna su resultado
  - Por qué: valida contrato y wiring básico entre capa de dominio y adaptador.
- [ ] UseCase.vista_previa delega correctamente con proveedor y nombre de archivo
  - Por qué: garantiza que la previsualización no tenga lógica adicional oculta en el caso de uso.
- [ ] UseCase.listar_hojas invoca al puerto con arg posicional (compatibilidad de firma)
  - Por qué: evitamos regresiones por cambio de signatura o uso de kwargs que rompan monkeypatches.
- [ ] UseCase.get_preview_for_sheet pasa `sheet_name` correcto y valida estructura mínima del retorno
  - Por qué: hoja seleccionada debe mapearse 1:1 con la previsualización; evita previews cruzadas.
- [ ] UseCase.get_or_prepare_config_for_sheet devuelve `existing_configs` del puerto y `suggested_new` con claves esperadas
  - Por qué: la UI depende de este shape para renderizar formularios; evita errores de clave ausente.
- [ ] UseCase.get_or_prepare_config_for_sheet respeta el `sheet_name` en `nombre_config` propuesto
  - Por qué: mejora trazabilidad entre hoja y configuración sugerida.
- [ ] UseCase.generar_csvs_por_hoja delega con `selecciones` sin mutaciones
  - Por qué: asegura que el mapeo hoja -> (config_id, start_row) llegue intacto al adaptador.
- [ ] UseCase.agendar_pendientes delega y retorna métrica/dict del puerto
  - Por qué: métricas de procesamiento deben consolidarse en servicios de infra, no en dominio.

Casos de error/edge (unit):
- [ ] listar_hojas devuelve lista vacía → no debe explotar; documentar comportamiento esperado del puerto
  - Por qué: algunos Excels pueden venir sin hojas válidas.
- [ ] get_preview_for_sheet con `sheet_name` inexistente → asegurar propagación controlada de excepción del puerto
  - Por qué: comportamiento consistente con validaciones de capa superior.
- [ ] selecciones vacías en generar_csvs_por_hoja → delega y retorna respuesta del puerto sin suposiciones
  - Por qué: la decisión de aceptar/rechazar vacío pertenece al adaptador/infra.

Notas:
- Mockear exclusivamente el puerto `ImportarExcelPort`; no tocar Django ni archivos reales.
- Mantener tests pequeños y de una sola responsabilidad.
