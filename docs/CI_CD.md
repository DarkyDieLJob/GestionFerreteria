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

## Migraciones en CD (staging/prod)
En este repositorio las migraciones están en `.gitignore` y pueden diferir entre entornos.
Por ese motivo, el deploy **no** depende de archivos de migración versionados y ejecuta las migraciones **in-situ** durante el despliegue.

### Qué se ejecuta
- `python src/manage.py migrate --run-syncdb --noinput`

### Por qué no se usa `makemigrations`
- Generar migraciones en runtime requeriría persistir archivos `migrations/` en el host o en un volumen, lo que complica el despliegue y puede generar divergencias difíciles de auditar.
- `--run-syncdb` permite crear las tablas faltantes sin necesidad de generar archivos de migración.

### Dónde vive
- Implementado en `.github/workflows/release-cicd.yml` para staging y producción, antes del `docker compose up -d` final.

### Notas de versionado
- El proyecto usa `standard-version` (ver `package.json`) para generar `CHANGELOG.md` y tags semánticos.
- La versión mostrada en UI se toma del `CHANGELOG.md` vía `src/core_app/context_processors.py`.
- Para que el bump (patch/minor/major) sea correcto, el merge a `release` debe conservar mensajes Conventional Commits (ver `docs/GIT_AGENTES.md`).
