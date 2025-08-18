# Estructura del Gestor de Ferretería

Este documento describe las apps base incluidas en el proyecto.

## Apps y modelos

### articulos
- Modelos
  - ArticuloBase (abstracto)
    - Campos: nombre, descripcion
  - Articulo
    - Campos: codigo_barras (único), des_acumulada, stock_consolidado, imagen
    - Meta: index en codigo_barras
    - Métodos: get_descuento, get_proveedor, generar_precios
  - ArticuloSinRevisar
    - Campos: proveedor(FK proveedores.Proveedor), codigo_proveedor, descripcion_proveedor, precio, stock, codigo_barras, estado, fecha_mapeo, descuento(FK precios.Descuento)
    - Meta: indexes en (proveedor, codigo_proveedor), estado, codigo_barras
    - Métodos: save, get_descuento, get_proveedor, generar_precios
    - Notas:
      - El campo usuario fue removido (no hay dependencia con auth.User).
      - En save(), si no hay descuento asociado, se utiliza por defecto "Sin Descuento" (creado por señales en precios).
  - ArticuloProveedor
    - Campos: articulo(FK articulos.Articulo, opcional), articulo_s_revisar(FK articulos.ArticuloSinRevisar, opcional), proveedor(FK proveedores.Proveedor), precio_de_lista(FK precios.PrecioDeLista), codigo_proveedor, descripcion_proveedor, precio, stock, dividir, descuento(FK precios.Descuento)
    - Meta: unique_together (proveedor, codigo_proveedor); index (proveedor, codigo_proveedor); constraint one_relation_required
    - Métodos: save, get_codigo_completo, generar_precios

### importaciones
- Modelos
  - ConfigImportacion
    - Campos: proveedor(FK proveedores.Proveedor), col_codigo, col_descripcion, col_precio, col_cant, col_iva, col_cod_barras, col_marca, ultima_actualizacion(auto_now)
    - Meta: unique_together (proveedor)

- Servicios
  - conversion.convertir_a_csv(input_path, sheet=0, ...)
    - Convierte xls/xlsx/ods a CSV (passthrough si ya es CSV) usando pandas (engines: openpyxl/xlrd/odf).
  - importador_csv.importar_csv(proveedor, ruta_csv, start_row, col_*_idx, ...)
    - Pipeline unificado de importación desde CSV con validación estricta por fila y upsert idempotente.

### precios
- Modelos
  - PrecioDeLista
    - Campos: codigo, descripcion, precio, proveedor(FK proveedores.Proveedor), iva, bulto, stock
    - Meta: unique_together (proveedor, codigo); index en codigo
    - Métodos: save, get_codigo_completo
  - Descuento
    - Campos: tipo, efectivo, bulto, cantidad_bulto, general, temporal, desde, hasta
    - Meta: indexes en tipo y (desde, hasta)
    - Métodos: save, is_active

### proveedores
- Modelos
  - Proveedor
    - Campos: nombre, abreviatura(única), descuento_comercial, margen_ganancia, margen_ganancia_efectivo, margen_ganancia_bulto
    - Meta: index en abreviatura
    - Métodos: save (normaliza abreviatura a mayúsculas)
  - Contacto
    - Campos: nombre, apellido, email, telefono
  - ContactoProveedor
    - Campos: proveedor(FK proveedores.Proveedor), contacto(FK proveedores.Contacto)
