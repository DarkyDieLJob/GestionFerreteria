# CI/CD

Este proyecto define dos flujos separados:

## 1) Simulacro (pre-release): `test-pipeline-*`

### Objetivo
Validar build/push y despliegue en staging sin ejecutar un release real.

### Trigger
- Tag con prefijo `test-pipeline-*`.

### Resultado
- Build & push de imagen a GHCR con el tag `test-pipeline-*`.
- Deploy a staging.
- NO hay backmerge.
- NO se despliega a producción por defecto.

## 2) Release real (release): `v*`

### Objetivo
Ejecutar un release real y despliegue end-to-end.

### Trigger
- Tag `v*`.

### Secuencia
1) Build & push de imagen a GHCR con el tag `vX.Y.Z`.
2) Deploy a staging.
3) Backmerge automático a `develop`.
4) Deploy a producción.
5) (Opcional) GitHub Release.

### Notas de versionado
- El proyecto usa `standard-version` (ver `package.json`) para generar `CHANGELOG.md` y tags semánticos.
- La versión mostrada en UI se toma del `CHANGELOG.md` vía `src/core_app/context_processors.py`.
