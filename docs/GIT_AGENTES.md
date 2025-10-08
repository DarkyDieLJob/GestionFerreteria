# GIT_AGENTES

Guía de flujo de trabajo Git para agentes y colaboradores.

## Convenciones de ramas
- Ramas largas vivas: `main` (producción), `pre-release` (integración/estabilización), `develop` (base para `feature/*` y `fix/*`).
- Ramas de trabajo: `feature/{app_o_seccion}/{descripcion}`.
  - Ejemplos: `feature/core_auth/reset-requests-badge`, `feature/doc/git-workflow`, `feature/core_auth/reset-flow-dni-wsp`.

### Ramas de corrección `fix/*`
- Objetivo: corregir defectos detectados en integración/QA antes del release.
- Origen: crear SIEMPRE a partir de `pre-release` (no desde `develop`).
- Nombre: `fix/{area}/{descripcion-corta}`.
- Flujo recomendado:
  1. `git checkout pre-release && git pull --ff-only`
  2. `git checkout -b fix/{area}/{descripcion}`
  3. Commits atómicos usando Conventional Commits (`fix:`, `docs:`, `chore:`)
  4. Abrir PR con base `pre-release`
  5. Tras merge, sincronizar `develop` si aplica (ver sección Sync)

> Nota (repos con 1 colaborador): se permiten merges directos cuando no haya revisor, manteniendo tests verdes y Conventional Commits.

## Crear una rama feature
1. Asegúrate de que `develop` está sincronizada con `pre-release`:
   - `git checkout develop`
   - `git fetch --all --prune`
   - `git pull --ff-only`
   - `git merge --no-ff origin/pre-release -m "Merge pre-release into develop"` (si hay cambios)
2. Crear la rama: `git checkout -b feature/{app}/{descripcion}`

### Excepción: ramas basadas en `pre-release`
- Útil para pruebas integrales sobre el estado actual de `pre-release`.
- Flujo:
  1. `git checkout pre-release && git pull --ff-only`
  2. `git checkout -b feature/{area}/tests-integracion-{alcance}`
  3. Commits con Conventional Commits (`test:`, `feat:`, etc.)
  4. PR con base `pre-release`
  5. Tras merge, sincronizar `develop` para mantener paridad.

## Algoritmo para PRs
- Si estás en `develop`, crea una `feature/*` para cualquier cambio.
- Si estás en `feature/*`, abre PR con base `pre-release`.
- Si trabajas en `pre-release` o `main`, sigue reglas de release o hotfix.

### Checklist mínimo para PRs
- **Tests**: ejecuta `python -m pytest -q` (o script equivalente) y confirma verde.
- **Commits**: usa Conventional Commits.
- **Migraciones**: incluye las migraciones de Django si se tocaron modelos.
- **Settings/env**: documenta variables nuevas (`settings.py` + `.env`).
- **Templates/admin**: actualiza si cambias campos visibles.
- **Alcance**: evita cambios fuera del scope del PR.
- **Verificación manual**: describe pasos y riesgos cuando sea necesario.

Pseudocódigo del flujo de PRs:
```
if branch == develop:
    create_feature_branch()
elif branch.startswith('feature/'):
    create_pr(base='pre-release')
else:
    follow_release_or_sync_rules()
```

## Sync entre ramas
- Mantener `develop` sincronizado con `pre-release`:
  - `git checkout develop`
  - `git fetch --all --prune`
  - `git merge --no-ff origin/pre-release -m "Merge pre-release into develop"`
- Evitar merges de `feature/*` directo a `main`.

## Releases
- Objetivo: promover cambios validados en `pre-release` hacia `main`.
- Pasos sugeridos:
  1. Validar CI verde + QA en `pre-release`.
  2. Crear PR de `pre-release` -> `main` (revisión final).
  3. Al mergear:
     - Crear tag semántico (`vX.Y.Z`): `git tag -a vX.Y.Z -m "Release vX.Y.Z"` y `git push origin vX.Y.Z`.
     - Opcional: GitHub Release con changelog.
  4. Desplegar desde `main`.

### Opción directa (sin PR)
```
git checkout pre-release
git pull --ff-only
# validar tests/QA
git checkout main
git pull --ff-only
git merge --no-ff pre-release -m "release: v1.0.0"
git tag -a v1.0.0 -m "release: v1.0.0"
git push origin main
git push origin v1.0.0
git checkout develop && git pull --ff-only && git merge --no-ff origin/pre-release -m "chore: sync pre-release -> develop (v1.0.0)" && git push
```

## Backport: ¿qué es y cuándo?
- Backport = llevar cambios ya integrados en una rama más adelantada a otra base.
- Ejemplos:
  - Merge de `pre-release` a `develop` cuando divergieron.
  - Hotfix en `main` que debe llevarse a `pre-release`/`develop`.
- Reglas:
  - Preferir merges limpios (`--no-ff`).
  - Documentar en el PR/commit que es un backport y link al PR original.

## Buenas prácticas
- Commits pequeños, descriptivos, con contexto.
- Ejecutar tests/coverage antes de cada push.
- No empujar directo a `main` ni `pre-release` sin PR (salvo escenario directo controlado).
- Borrar ramas `feature/*` tras merge (local y remoto).

## Comandos útiles
- Crear feature: `git checkout develop && git pull --ff-only && git checkout -b feature/{app}/{desc}`
- PR a `pre-release`: `gh pr create --base pre-release --head feature/{app}/{desc} ...`
- Sync `pre-release` -> `develop`: `git checkout develop && git fetch && git merge --no-ff origin/pre-release -m "Merge pre-release into develop"`
- Release manual: `git checkout pre-release && git pull --ff-only && git checkout main && git merge --no-ff pre-release ...`
- Crear fix: `git checkout pre-release && git pull --ff-only && git checkout -b fix/{area}/{desc}`
- PR fix: `gh pr create --base pre-release --head fix/{area}/{desc} ...`

## Versionado y changelog (standard-version)
- Versionado y `CHANGELOG.md` se manejan exclusivamente con `standard-version` siguiendo Conventional Commits.

### Política
- No crear tags manuales para releases regulares.
- No editar `CHANGELOG.md` a mano.
- Usar semántica `major.minor.patch`.

### Flujo recomendado
1. Asegurar que `main` tiene el contenido a publicar (merge `pre-release` -> `main`).
2. En `main`, ejecutar `npx standard-version` (o `--release-as patch|minor|major`).
3. Publicar commit y tags: `git push --follow-tags origin main`.
4. Sincronizar ramas:
   - `git checkout develop && git pull --ff-only && git merge --no-ff origin/main -m "chore: sync main -> develop (release)" && git push`
   - Opcional: `git checkout pre-release && git pull --ff-only && git merge --no-ff origin/main -m "chore: sync main -> pre-release (release)" && git push`

### Notas
- Evitar mezclar tags manuales con `standard-version`.
- Conventional Commits permiten inferir el tipo de release automáticamente.
