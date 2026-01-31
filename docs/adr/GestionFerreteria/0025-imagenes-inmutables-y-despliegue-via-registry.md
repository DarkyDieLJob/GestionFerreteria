# Architecture Decision Record (ADR): Imágenes inmutables y despliegue vía registry (GHCR)

## Estado
Aceptado

## Contexto
- Los despliegues actuales construyen la imagen “in situ” en el runner, lo que incrementa los tiempos (≈10 min por build) y agrega variabilidad.
- Queremos estandarizar un flujo reproducible y eficiente que funcione para todos los hijos del repositorio padre (DjangoProyects): construir una sola vez, publicar en un registry, y desplegar solo con pull + up (sin build).
- Se requiere soporte multi-arquitectura (amd64/arm64, y opcionalmente arm/v7) y autenticación segura contra el registry.

## Decisión
- Adoptar el modelo de “imagen inmutable” como artefacto de despliegue.
- Usar GitHub Container Registry (GHCR, ghcr.io) como registry primario.
- Autenticación: secreto GHCR_PAT configurado en el repositorio (o a nivel organización) con permisos write:packages.
- Habilitar builds multi-arch mediante Docker Buildx en el job de Build & Push (no en Deploy).
- Separar los workflows en dos responsabilidades:
  - Build & Push: construye la imagen (multi-arch) y publica múltiples tags.
  - Deploy: realiza docker login + docker compose pull + docker compose up -d --no-build (sin compilar en destino).
- No utilizar el tag “latest” en producción. Producción debe “pinnear” una versión explícita (vX.Y.Z). Se permite publicar latest como alias de conveniencia, pero no debe usarse en prod.

## Estrategia de tags
- Staging / testing:
  - Publicar múltiples tags por build: `test-YYYYMMDD-N`, `sha-<7>`, `staging-latest`.
  - Deploy de staging: usar `IMAGE_TAG=staging-latest` (alias mutable) o el tag exacto `test-YYYYMMDD-N` si se quiere fijar una build concreta.
- Producción:
  - Publicar `vX.Y.Z` (y opcionalmente `latest` como co-tag, no utilizado por prod).
  - Deploy de prod: usar `IMAGE_TAG=vX.Y.Z` (pinneado) o incluso el digest (`@sha256:...`) si se requiere inmutabilidad estricta.

## Cambios propuestos en compose
- Parametrizar la imagen de la app y compartirla entre servicios `app` (web) y `worker` (comandos distintos, misma imagen):

```yaml
services:
  app:
    image: ${IMAGE_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}
    # command/ports/env/volumes/healthchecks según corresponda

  worker:
    image: ${IMAGE_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}
    # command/env/healthchecks según corresponda

  db:
    image: postgres:16

  redis:
    image: redis:7-alpine
```

- Variables recomendadas (en .env o inyectadas por el workflow):
  - `IMAGE_REGISTRY=ghcr.io`
  - `IMAGE_REPO=<org>/<app>` (p.ej. `tu-org/gestionferreteria`)
  - `IMAGE_TAG=<staging-latest | test-YYYYMMDD-N | vX.Y.Z>`

## Cambios propuestos en workflows
- Reusable Build & Push (padre):
  - docker/login-action a GHCR con `GHCR_PAT`.
  - docker/build-push-action con `--platform linux/amd64,linux/arm64[,linux/arm/v7]` y `push: true`.
  - Publicar múltiples tags según el evento (testing vs release).
- Reusable Deploy (padre):
  - docker login (lectura).
  - `docker compose pull` + `docker compose up -d --no-build`.
  - Healthchecks + smoke test como en ADR0023.
  - Opciones: `force_redeploy`, `skip_build_if_image_present` (por compatibilidad/hardening si se mantiene ruta de build in situ en POCs).

## Política de disparo (triggers)
- Build & Push:
  - pre-release: al hacer push a la rama `pre-release` o crear tag `test-*` se construye y publica multi-arch con tags `staging-latest`, `test-YYYYMMDD-N`, `sha-<7>`.
  - release: al hacer push/merge a la rama `release` y/o crear un tag semántico `vX.Y.Z`, se construye y publica multi-arch con tag `vX.Y.Z` (y opcionalmente `latest` como co-tag no consumido por prod).
- Deploy (pull + up, sin build):
  - deploy: al hacer push a la rama `deploy` (o por `workflow_dispatch`) se ejecuta el despliegue usando `IMAGE_TAG` indicado en el input del workflow.
  - Staging: `IMAGE_TAG=staging-latest` o un `test-YYYYMMDD-N` concreto.
  - Producción: `IMAGE_TAG=vX.Y.Z` fijado y gate manual de aprobación.

Rationale: separar construcción (costosa) de despliegue (rápido y predecible), y evitar builds "in situ" en los runners de despliegue.

## Consecuencias
- Despliegues más rápidos y previsibles (sin “Build image (in-situ)” en deploy).
- Rollbacks sencillos cambiando `IMAGE_TAG` (p.ej. `vX.Y.Z -> vX.Y.(Z-1)`).
- Mayor trazabilidad y compliance (artefactos versionados y escaneables en GHCR).
- Staging puede seguir iterando rápidamente con alias `staging-latest` o tags efímeros; producción pinneada a versiones explícitas.

## Consideraciones adicionales
- Runners self-hosted: cache de capas Docker y buildx puede acelerar builds de testing; en Deploy ya no se construye.
- Volúmenes y datos: continúan separados de la imagen (DB/redis/media/logs), manteniendo la app stateless.
- Multi-arch: se publica un manifest list por tag; cada host tira de su variante (amd64/arm64/etc.).

### Requisitos de runners y secretos
- Secretos requeridos:
  - `GHCR_PAT`: Token con `write:packages` para Build & Push; con `read:packages` basta para Deploy si se configura por ambiente.
  - `COMPOSE_ENV` o variables de entorno inyectadas (DATABASE_URL, BROKER_URL, etc.).
- Runners:
  - Build & Push: runner con Docker Buildx y QEMU habilitados para multi-arch; espacio en disco suficiente (≥20 GB) y cache de buildx persistente.
  - Deploy: runner con Docker/Compose, acceso a red del entorno, permisos para `docker login` y `pull` desde GHCR. No requiere buildx.
  - Etiquetado sugerido: `stage` para staging; `prod` para producción.

### Matriz multi-arquitectura (ejemplo Build & Push)
```yaml
strategy:
  matrix:
    platform: [linux/amd64, linux/arm64]
steps:
  - uses: docker/setup-qemu-action@v3
  - uses: docker/setup-buildx-action@v3
  - uses: docker/build-push-action@v6
    with:
      platforms: ${{ join(matrix.platform, ',') }}
      push: true
```

### Compatibilidad docker compose
- Usar formato compose v2 y `docker compose` (no `docker-compose`).
- Evitar `build:` en servicios de `app` y `worker` en entornos que sigan este ADR; usar `image:` parametrizado.
- Variables soportadas vía `.env` o `env` del workflow: `IMAGE_REGISTRY`, `IMAGE_REPO`, `IMAGE_TAG`.

## Plan de adopción
1) Implementar los reusables Build & Push y Deploy en el padre (DjangoProyects).
2) Portar a los hijos: actualizar compose para usar `image:` con `${IMAGE_REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}` y ajustar workflows a los reusables.
3) Configurar `GHCR_PAT` y probar en staging (`IMAGE_TAG=staging-latest`).
4) Definir versión `vX.Y.Z` y desplegar en prod con tag pinneado.

### Métricas y validación
- Tiempo de deploy (objetivo: < 2 min desde `deploy` push hasta contenedores healthy).
- Tasa de fallos en deploy por build: 0, al eliminar builds en destino.
- Reproducibilidad: poder redeployar el mismo `vX.Y.Z` con hash/digest idéntico.
- Tiempo de build multi-arch y efectividad de cache (baseline vs optimizado con buildx-cache).

## Flujo de trabajo propuesto (end-to-end)
- Desarrollo (local/feature):
  - Base: `develop`. Crear ramas `feature/<nombre>` desde `develop`.
  - CI: lint/tests. Opcional: builds de prueba (sin push a registry) para validar Dockerfile.
- Integración: `pre-release`
  - Merge de features en `pre-release` para verificación integral.
  - CI: lint/tests + (opcional) Build & Push a GHCR con tag `staging-latest` y `test-YYYYMMDD-N`.
  - Deploy a staging: usar reusable Deploy (pull + up --no-build) con `IMAGE_TAG=staging-latest` o `test-YYYYMMDD-N`.
- Candidata a release: `release`
  - Al promover desde `pre-release` → `release`, se ejecuta CI completo.
  - Si pasa, el job Build & Push publica imagen multi-arch con tags `vX.Y.Z` (y opcionalmente `latest`).
  - Se crea tag anotado y changelog.
- Hotfix: `hotfix/<nombre>`
  - Deriva desde `release` (o desde el último tag) cuando la release falla o se detecta incidencia crítica.
  - Pasa por el mismo flujo de CI y, si procede, publica una nueva `vX.Y.Z+patch`.
- Deploy: `deploy`
  - Rama que activa los runners de staging/prod y ejecuta el reusable Deploy con `IMAGE_TAG` apropiado.
  - Staging: `IMAGE_TAG=staging-latest` o tag de prueba.
  - Producción: `IMAGE_TAG=vX.Y.Z` (pinneado) y gate manual.

Notas:
- Los runners de staging y prod deben apuntar a la rama `deploy`. Se sugiere mantener `main` como histórica/compatibilidad y no renombrarla de inmediato; `release` asume el rol de rama de releases estables para automatizar publish y etiquetado. Una vez estabilizado el flujo, evaluar si `main` queda obsoleta o se alinea a `release`.
- En producción, no usar `latest` en `IMAGE_TAG`. Se permite co-tag `latest` al publicar, pero `deploy` debe consumir `vX.Y.Z`.

### Riesgos y mitigaciones
- Riesgo: fuga de permisos del `GHCR_PAT`.
  - Mitigación: mínimos privilegios; separar tokens de build (write) y deploy (read); rotación periódica.
- Riesgo: inconsistencias por uso accidental de `latest`.
  - Mitigación: gates y validaciones que rechacen `IMAGE_TAG=latest` en job de producción.
- Riesgo: aumento de tiempo en primera build multi-arch.
  - Mitigación: cache persistente de buildx, warm-up en runners.
