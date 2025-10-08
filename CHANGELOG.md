# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### 1.0.1 (2025-10-08)


### Features

* add cron-ready script for pending CSVs processing ([4d43b53](https://github.com/DarkyDieLJob/GestionFerreteria/commit/4d43b5339c2172f0a868816b87ededb2e4541036))
* add dynamic forms for multi-sheet config ([a1a0d17](https://github.com/DarkyDieLJob/GestionFerreteria/commit/a1a0d17b30e5106c17b21d0317b9fe859b598889))
* add multi-config support and pending files model ([cb8dcd6](https://github.com/DarkyDieLJob/GestionFerreteria/commit/cb8dcd60b0a19284d40d2b5bc18690b81b6b08f1))
* add multi-sheet handling in repository ([d3a58f6](https://github.com/DarkyDieLJob/GestionFerreteria/commit/d3a58f6b94cea545f88f22f64f866ad58f21dede))
* add styled templates for import flow ([5bf438a](https://github.com/DarkyDieLJob/GestionFerreteria/commit/5bf438aa99de49a208c25b3754bc300b1d5c438f))
* **admin:** auto-register all models for importaciones, articulos, precios and proveedores ([3d1a7eb](https://github.com/DarkyDieLJob/GestionFerreteria/commit/3d1a7eb03a5592e1471faecefa42f2fa18f328e4))
* aplicar cambios recientes en articulos, importaciones, precios y proveedores; actualizar tests y configuraciones ([bb036f5](https://github.com/DarkyDieLJob/GestionFerreteria/commit/bb036f5793088cce6e3ef48a3d19ecd44f589d31))
* **articulos:** agregar puertos hexagonales de dominio (fase 1/4) ([4bb2f81](https://github.com/DarkyDieLJob/GestionFerreteria/commit/4bb2f816b1c843e0aca6c03864231c4f696a6563))
* **articulos:** casos de uso hexagonales que delegan en puertos (fase 1/4) ([665d4b8](https://github.com/DarkyDieLJob/GestionFerreteria/commit/665d4b8a0e8e1fe97678420011b8341da76fb5a8))
* **articulos:** estiliza vistas de búsqueda y mapeo; aplica Tailwind a widgets del formulario ([4abe60a](https://github.com/DarkyDieLJob/GestionFerreteria/commit/4abe60aa8f7452593e261b852ab1909d9604a6f7))
* **articulos:** repositorios Django para puertos (precio, busqueda, mapeo) (fase 1/4) ([09b133a](https://github.com/DarkyDieLJob/GestionFerreteria/commit/09b133afdb5b210796fccb08e2a0d9786f108600))
* enhance forms for per-sheet ConfigImportacion editing ([d45affc](https://github.com/DarkyDieLJob/GestionFerreteria/commit/d45affc1b1dcf5d6c33d9f16a6b0a62228e47365))
* extend use cases for multi-sheet import flow ([21a435f](https://github.com/DarkyDieLJob/GestionFerreteria/commit/21a435f6967106d00d75a9707658ef4110b1c792))
* extend use cases for per-sheet config editing in preview ([4f46293](https://github.com/DarkyDieLJob/GestionFerreteria/commit/4f46293cd77c0065d9c55f291cbc6063046f3f70))
* **importaciones:** add spreadsheet-to-csv conversion for xls/xlsx/ods\n\nAdds convertir_a_csv service with lazy pandas import and engines (openpyxl/xlrd/odf). Includes unit test with mocked pandas and real-file tests that generate xls/xlsx/ods dynamically and verify full pipeline (convert + importar_csv) for 3 layouts with banners. Tests auto-skip when deps are missing. ([557e788](https://github.com/DarkyDieLJob/GestionFerreteria/commit/557e7883447e157214fa7b1095d401271438cd36))
* **importaciones:** autocomplete config form on selection via native JS + JSON endpoint; filter configs by proveedor ([e8e1548](https://github.com/DarkyDieLJob/GestionFerreteria/commit/e8e15480aa52dc7ecdfcc7410105bfb27056d0bf))
* **importaciones:** borrar archivo fuente (xlsx/xls/ods) tras generar CSVs y crear pendientes; mantener borrado de CSV tras procesamiento ([6ea6afa](https://github.com/DarkyDieLJob/GestionFerreteria/commit/6ea6afa80450510441e481478ae9beef00f899ee))
* **importaciones:** caso de uso ImportarExcelUseCase (fase 2/4) ([6cf6567](https://github.com/DarkyDieLJob/GestionFerreteria/commit/6cf6567e14924b14bc5b08c978a56d3c6fe8adfa))
* **importaciones:** CSV importer with strict validation and idempotent upsert\n\nImplements importar_csv service (start_row, column indices, strict type checks for codigo/descripcion/precio). Adds 3 realistic CSV fixtures (layouts 1-3 with banners) and integration tests validating counts and DB side effects. Also ensures default 'Sin Descuento' exists in tests. ([8cef568](https://github.com/DarkyDieLJob/GestionFerreteria/commit/8cef568251b0271bdee4ab508f87af280f2e2581))
* **importaciones:** ExcelRepository implementa ImportarExcelPort (fase 2/4) ([662e0a7](https://github.com/DarkyDieLJob/GestionFerreteria/commit/662e0a7711df68412b88bf4eef5a861bb171f691))
* **importaciones:** landing para seleccionar proveedor y comenzar importación\n\n- Vista ImportacionesLandingView con selector de proveedor (DB negocio_db)\n- Ruta '' en importaciones con name=landing\n- Template Tailwind importaciones/landing.html\n- Navbar apunta a importaciones:landing\n- Tests ejecutados: OK (>=90% cobertura) ([c8c4550](https://github.com/DarkyDieLJob/GestionFerreteria/commit/c8c4550dc11b2ef171fe455a20fa775ff812615c))
* **importaciones:** mostrar nombre de archivo y hoja en confirmación; agregar editar/eliminar pendiente ([a67405b](https://github.com/DarkyDieLJob/GestionFerreteria/commit/a67405b3fe7f4d1f183c326f4af6611f64a7cfb9))
* **importaciones:** per-sheet edit now uses preview UI; remove simplified edit view and route; add nombre_archivo_origen tracking and link from confirm; JS focus by #hoja; clean up templates ([88be225](https://github.com/DarkyDieLJob/GestionFerreteria/commit/88be2257d904d2d9e752423385b3852a9f188a46))
* **importaciones:** programar procesamiento diario de Excel a las 00:00 con schedule y script CLI ([9b0a89f](https://github.com/DarkyDieLJob/GestionFerreteria/commit/9b0a89fdcac5a38f8bd34c43aaf2084b9a6c09f9))
* **importaciones:** vistas y estilos de importaciones; navbar link\n\n- Cambio a FormView en ImportacionCreateView para compatibilidad con forms no-modelo\n- Estilos Tailwind en templates de importaciones (form y preview) inspirados en core_auth\n- Link de Importaciones en navbar (desktop y móvil)\n- Añadido pandas a requirements (dev/notebook/runtime)\n- Integración de urls de importaciones en core_config ([6025d6c](https://github.com/DarkyDieLJob/GestionFerreteria/commit/6025d6c717b70c87eab4cf68a9282e4edbce3580))
* **precios/ui): estilos CRUD de Descuento + enlace en navbar; fix(navbar:** evitar solapamiento con items de staff ([d8ceb5d](https://github.com/DarkyDieLJob/GestionFerreteria/commit/d8ceb5d9e23e7112979a90dced016c417835d679))
* **precios/ui): estilos CRUD de Descuento + enlace en navbar; fix(navbar:** evitar solapamiento con items de staff ([423e132](https://github.com/DarkyDieLJob/GestionFerreteria/commit/423e1329fa08fbc7cc33ca49d4b32fdacc2a84c7))
* **precios:** señal post_migrate para crear Descuento por defecto en negocio_db ([71773a1](https://github.com/DarkyDieLJob/GestionFerreteria/commit/71773a1582a0d2b02776ae6e96c2659e63f874f9))
* **proveedores:** CRUD vistas, urls, templates y tests; estilos UI y navbar; shim de modelos para compatibilidad ([3352879](https://github.com/DarkyDieLJob/GestionFerreteria/commit/3352879b3823aa8ebe3b602854900204cfd16e37))
* scaffold basic apps for ferreteria with models and model tests ([fee48f4](https://github.com/DarkyDieLJob/GestionFerreteria/commit/fee48f4228604cff0929895a79e918e378e63b00))
* unify database configuration ([e6ac7e8](https://github.com/DarkyDieLJob/GestionFerreteria/commit/e6ac7e866850c79b4eaa717a3a37d0f82144a394))
* update preview template for per-sheet forms and tables with Tailwind ([ab1b57c](https://github.com/DarkyDieLJob/GestionFerreteria/commit/ab1b57c23bbd025785703560ee0109b2a09997fe))


### Bug Fixes

* **admin:** ensure adapter models are imported before auto-registering models ([8182e77](https://github.com/DarkyDieLJob/GestionFerreteria/commit/8182e77d28d31c690ef86ca440bb6ff945e25162))
* align preview data with template to avoid dict indexing in Jinja/Django templates ([d2c6bfd](https://github.com/DarkyDieLJob/GestionFerreteria/commit/d2c6bfdb07f342b0f037fc8aeccc991273ef2c50))
* **ci:** install Pillow for ImageField to allow migrate --run-syncdb in CI ([2538c04](https://github.com/DarkyDieLJob/GestionFerreteria/commit/2538c0460bb72f3e1c449cfc99d951d1ec24e851))
* **ci:** reuse pre-synced SQLite DB in pytest; set TEST.NAME and use --reuse-db ([ac74553](https://github.com/DarkyDieLJob/GestionFerreteria/commit/ac745538c9d1fa20a574db1f3d81eafae97f05bf))
* **ci:** sync test DB schema in CI before pytest using migrate --run-syncdb ([c30d65e](https://github.com/DarkyDieLJob/GestionFerreteria/commit/c30d65e6179ea4efa3286f05adbc702043f8c2a1))
* expose models via models.py for precios/articulos/importaciones (import adapters.models) ([4c6ab01](https://github.com/DarkyDieLJob/GestionFerreteria/commit/4c6ab01141e57a7b0b73b4a5dd4f10e0a8e9bd91))
* **importaciones:** mostrar hoja_origen y hacer la hoja no editable en edición de pendiente ([dc3185e](https://github.com/DarkyDieLJob/GestionFerreteria/commit/dc3185e4eee4177cf7ef8e25b4f19ea4d9b1fb7f))
* **importaciones:** soportar .xls y .ods seleccionando engine de pandas (xlrd/odf/openpyxl) en vista previa y listado de hojas ([3a08d03](https://github.com/DarkyDieLJob/GestionFerreteria/commit/3a08d0393265b07f12f900029a09c1b4f51d1c8c))
* **precios/form:** usar DateInput HTML5 para 'desde' y 'hasta' con estilo ancho completo ([1c654cb](https://github.com/DarkyDieLJob/GestionFerreteria/commit/1c654cb250212265c483b9a59f4766533d4e7ca5))
* **precios:** aplicar descuento y bulto correctamente en ArticuloProveedor; usar overrides y Decimal; ocultar logs y mostrar tipo de descuento en búsqueda ([682739b](https://github.com/DarkyDieLJob/GestionFerreteria/commit/682739b8c42ec88803c030ecbaf27e1514ae1165))
* preview template dict access and default usage causing TemplateSyntaxError ([d9c94ff](https://github.com/DarkyDieLJob/GestionFerreteria/commit/d9c94ff5a05d62e850c316e0fac63d6bc9dbbab2))
* **proveedores:** corregir render del formulario usando widgets en Meta y {{ field }} en template ([b767067](https://github.com/DarkyDieLJob/GestionFerreteria/commit/b767067bc1995a669adc992f5db20b34d3584e9a))
* **proveedores:** incluir urls y ajustes finales en views para CRUD ([40f9571](https://github.com/DarkyDieLJob/GestionFerreteria/commit/40f9571bf0feb5f0aa13b1f68ba6fed617e2a913))

### [1.2.5](https://github.com/DarkyDieLJob/DjangoProyects/compare/v1.2.4...v1.2.5) (2025-08-13)

### [1.2.4](https://github.com/DarkyDieLJob/DjangoProyects/compare/v1.2.3...v1.2.4) (2025-08-13)

### [1.2.3](https://github.com/DarkyDieLJob/DjangoProyects/compare/v1.2.2...v1.2.3) (2025-08-11)


### Bug Fixes

* **ci:** back-merge automático main -> pre-release con GitHub Actions ([413fae2](https://github.com/DarkyDieLJob/DjangoProyects/commit/413fae2a73622cb2c2ef6c4ebcf0956c74f8b8db))

### [1.2.2](https://github.com/DarkyDieLJob/DjangoProyects/compare/v1.2.1...v1.2.2) (2025-08-11)


### Bug Fixes

* **ci:** otorgar permissions contents:write para crear releases con action-gh-release ([e14e3b9](https://github.com/DarkyDieLJob/DjangoProyects/commit/e14e3b9c119eeb4b9423258405912c5b9114addd))
* **context:** reconocer encabezados standard-version en CHANGELOG (### [x.y.z]) ([dc30e5d](https://github.com/DarkyDieLJob/DjangoProyects/commit/dc30e5df978079358b3b68de51f4e6330714eabc))

### [1.2.1](https://github.com/DarkyDieLJob/DjangoProyects/compare/v1.2.0...v1.2.1) (2025-08-11)


### Features

* **deps:** crear requirements/runtime.txt para producción ([6a0c210](https://github.com/DarkyDieLJob/DjangoProyects/commit/6a0c2105fbb6a81406533a49ade50158c87a659a))
* **docker:** agregar Dockerfile y entrypoint con build de Tailwind ([77e6536](https://github.com/DarkyDieLJob/DjangoProyects/commit/77e6536c9c1ecfa6c6767fc0965ab573183b718f))


### Bug Fixes

* **config:** cargar src/.env con AutoConfig para exponer app_name y credenciales ([77beb30](https://github.com/DarkyDieLJob/DjangoProyects/commit/77beb3046a04bd929547f2377df46661bffc634d))

## [1.2.0](https://github.com/DarkyDieLJob/DjangoProyects/compare/v1.1.0...v1.2.0) (2025-08-10)

## v1.0.0 (2025-08-10)

### Feat

- **ui**: show app version from CHANGELOG.md in base template
