# ADR-0001: Separación de Aplicaciones con Múltiples Bases de Datos SQLite

## Estado
Propuesto

## Contexto
El sistema de gestión de ferretería debe manejar un volumen significativo de datos, con aproximadamente 65,000 registros en `PrecioDeLista`, aunque los artículos reales se consolidan en ~6,000-7,000 en `Articulo`. Los requerimientos incluyen:

- **Códigos de proveedor**: Almacenar códigos con `/` al final (e.g., `37/`, `0037-25/`) en `PrecioDeLista.codigo` y `ArticuloProveedor.codigo_proveedor`, con abreviaturas dinámicas (e.g., `37/Vj`) via `get_codigo_completo()`.
- **Precios dinámicos**: Calcular precios (`base`, `final`, `final_efectivo`, `bulto`, `final_bulto`, `final_bulto_efectivo`) considerando márgenes, descuentos por proveedor, bultos, y descuentos temporales.
- **Importación masiva**: Procesar archivos Excel con Celery (`procesar_excel`) para `PrecioDeLista` y `ArticuloSinRevisar`, con vista previa y columnas configurables via `ConfigImportacion`.
- **Búsquedas**: Soportar búsquedas flexibles (`BuscarArticuloView`) con/sin abreviatura (e.g., `37`, `37/Vj`).
- **Mapeo**: Convertir `ArticuloSinRevisar` a `Articulo` con descripciones acumuladas.
- **Concurrencia**: Evitar bloqueos de escritura en SQLite durante cargas masivas.

SQLite, usado como base de datos, tiene limitaciones de concurrencia (bloqueos a nivel de base de datos). Las cargas masivas (e.g., importación de Excel) pueden causar conflictos, especialmente al escribir en `PrecioDeLista` y `ArticuloSinRevisar`. La arquitectura hexagonal requiere separar la lógica de negocio (`domain/`) de los adaptadores (`adapters/`), y el proyecto debe ser modular para facilitar mantenimiento y escalabilidad.

## Decisión
Dividiremos el proyecto en aplicaciones Django (`proveedores`, `articulos`, `precios`, `importaciones`) con bases de datos SQLite separadas (`proveedores_db.sqlite3`, `articulos_db.sqlite3`, `precios_db.sqlite3`, `importaciones_db.sqlite3`) para minimizar bloqueos de escritura. Cada aplicación tendrá responsabilidades específicas, siguiendo la arquitectura hexagonal, con casos de uso en `domain/` y adaptadores en `adapters/`. Un enrutador de bases de datos (`AppRouter`) gestionará las relaciones entre modelos.

### Estructura de Aplicaciones
- **proveedores**:
  - Modelos: `Proveedor`, `Contacto`, `ContactoProveedor`.
  - Base: `proveedores_db.sqlite3`.
  - Responsabilidades: Gestión de proveedores y contactos.
- **articulos**:
  - Modelos: `ArticuloBase`, `Articulo`, `ArticuloSinRevisar`, `ArticuloProveedor`.
  - Base: `articulos_db.sqlite3`.
  - Responsabilidades: Gestión de artículos, mapeo, búsquedas, precios dinámicos.
- **precios**:
  - Modelos: `PrecioDeLista`, `Descuento`.
  - Base: `precios_db.sqlite3`.
  - Responsabilidades: Gestión de precios y descuentos.
- **importaciones**:
  - Modelos: `ConfigImportacion`.
  - Base: `importaciones_db.sqlite3`.
  - Responsabilidades: Configuración y procesamiento de importaciones de Excel.
- **core_auth** (existente):
  - Modelos: Usa `django.contrib.auth.models.User`.
  - Base: `auth_db.sqlite3`.
  - Responsabilidades: Autenticación.
- **core_app** (existente):
  - Sin base propia; usa modelos de otras apps.
  - Responsabilidades: Dashboard y vistas generales.

### Configuración de Bases de Datos
- Cada aplicación usa una base SQLite independiente para evitar bloqueos.
- Configuración en `settings.py`:
  ```python
  DATABASES = {
      'default': {},
      'auth_db': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'core_auth/auth_db.sqlite3'},
      'proveedores_db': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'proveedores/proveedores_db.sqlite3'},
      'articulos_db': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'articulos/articulos_db.sqlite3'},
      'precios_db': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'precios/precios_db.sqlite3'},
      'importaciones_db': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'importaciones/importaciones_db.sqlite3'},
  }
  DATABASE_ROUTERS = ['core_config.database_routers.AppRouter']
  ```
- Enrutador (`AppRouter` en `database_routers.py`):
  - Asigna modelos a sus bases según `app_label`.
  - Permite relaciones entre apps (e.g., `ArticuloProveedor` -> `PrecioDeLista`).
  - Controla migraciones por base.

### Modelos y Lógica
- **Códigos**: `PrecioDeLista.codigo` y `ArticuloProveedor.codigo_proveedor` almacenan códigos con `/` (e.g., `37/`, `0037-25/`). Método `get_codigo_completo()` genera códigos con abreviatura (e.g., `37/Vj`).
- **Precios dinámicos**: `ArticuloBase.generar_precios` calcula precios (`base`, `final`, `final_efectivo`, `bulto`, `final_bulto`, `final_bulto_efectivo`) usando `Descuento` y `Proveedor` (márgenes, descuentos, IVA, bultos).
- **Descuentos**: `Descuento` con `tipo="Sin Descuento"` como fallback, creado vía señal `post_migrate`. Soporta descuentos temporales (`temporal`, `desde`, `hasta`).
- **Búsquedas**: `BuscarArticuloView` en `articulos/adapters/views.py` soporta consultas con/sin abreviatura, usando `using()` para bases específicas.
- **Importación**: `procesar_excel` (Celery) escribe en `precios_db` y `articulos_db` con transacciones atómicas, usando `ConfigImportacion` para mapear columnas.

### Arquitectura Hexagonal
- **Dominio** (`domain/`):
  - Casos de uso: `CalcularPrecioUseCase`, `BuscarArticuloUseCase`, `MapearArticuloUseCase`, `ImportarExcelUseCase`.
  - Puertos: `CalcularPrecioPort`, `BuscarArticuloPort`, etc., en `domain/interfaces.py`.
- **Adaptadores** (`adapters/`):
  - Repositorios: Implementan puertos (e.g., `PrecioRepository`, `ArticuloRepository`) con consultas Django.
  - Vistas: `BuscarArticuloView`, `importar_excel`, `mapear_articulo`.
- Flujo: Vistas -> Casos de uso -> Repositorios -> Modelos.

## Consecuencias
### Ventajas
- **Concurrencia**: Múltiples bases SQLite evitan bloqueos en cargas masivas (`procesar_excel`).
- **Modularidad**: Aplicaciones separadas (`proveedores`, `articulos`, `precios`, `importaciones`) reflejan dominios funcionales.
- **Escalabilidad**: Índices en modelos optimizan búsquedas; Celery maneja tareas pesadas.
- **Mantenibilidad**: Hexagonal desacopla lógica de negocio; relaciones explícitas facilitan migraciones.
- **Flexibilidad**: `Descuento` y `generar_precios` soportan precios dinámicos y ofertas temporales.

### Desventajas
- **Complejidad**: Gestionar múltiples bases requiere `using()` explícito en consultas cruzadas.
- **Rendimiento**: SQLite no es ideal para alta concurrencia; PostgreSQL podría ser necesario si el volumen crece.
- **Sincronización**: Cambios en `Proveedor.abreviatura` requieren recargar vistas/caché.

### Mitigaciones
- Usar `using()` en consultas cruzadas y transacciones atómicas.
- Cachear precios frecuentes (e.g., Redis) si el rendimiento es crítico.
- Evaluar PostgreSQL para volúmenes mayores o alta concurrencia.

## Alternativas Consideradas
1. **Base de datos única**:
   - Simplifica configuración, pero causa bloqueos en SQLite durante cargas masivas.
   - Rechazada por limitaciones de concurrencia.
2. **Base compartida para `precios` e `importaciones`**:
   - Reduce bases, pero `PrecioDeLista` recibe escrituras masivas, lo que podría bloquear `ConfigImportacion`.
   - Rechazada para maximizar aislamiento.
3. **PostgreSQL**:
   - Mejor concurrencia, pero aumenta complejidad de despliegue para un sistema inicial.
   - Considerar como futura migración.

## Recomendaciones
1. **Implementar estructura**:
   - Crear apps (`proveedores`, `articulos`, `precios`, `importaciones`) con `python manage.py startapp`.
   - Mover modelos a sus apps, ajustando `ForeignKey` con `app_label`.
2. **Configurar bases**:
   - Actualizar `settings.py` y `database_routers.py`.
   - Ejecutar migraciones por base (`python manage.py migrate --database=<db>`).
3. **Implementar casos de uso**:
   - Crear puertos/adaptadores en `domain/` y `adapters/`.
   - Usar `BuscarArticuloView`, `importar_excel`, `procesar_excel`.
4. **Pruebas**:
   - Importar Excel pequeño (~100 registros).
   - Verificar búsquedas (`37`, `37/Vj`), precios dinámicos, y mapeo.
   - Usar `pytest` para pruebas unitarias.
5. **Monitoreo**:
   - Usar `EXPLAIN` en SQLite para optimizar consultas.
   - Evaluar Redis para caché si el rendimiento es crítico.

## Referencias
- Modelos: `src/proveedores/models.py`, `src/articulos/models.py`, `src/precios/models.py`, `src/importaciones/models.py`.
- Estructura: `src/ESTRUCTURA.md`.
- Requerimientos: Códigos con `/`, precios dinámicos, importación masiva, búsquedas flexibles.