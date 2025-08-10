# GIT_AGENTES

Guía de flujo de trabajo Git para agentes y colaboradores.

## Convenciones de ramas
- Ramas largas vivas: `main` (producción), `pre-release` (staging), `develop` (integración)
- Ramas de trabajo: `feature/{app_o_seccion}/{descripcion}`
  - Ejemplos:
    - `feature/core_auth/reset-requests-badge`
    - `feature/doc/git-workflow`
    - `feature/core_auth/reset-flow-dni-wsp`

## Crear una rama feature
1) Asegúrate de estar en `develop` actualizado con `pre-release` (ver Sync):
   - `git checkout develop`
   - `git fetch --all --prune`
   - `git pull --ff-only`
   - `git merge --no-ff origin/pre-release -m "Merge pre-release into develop"` (si hay cambios en pre-release)
2) Crea la rama:
   - `git checkout -b feature/{app}/{descripcion}`

## Algoritmo para PRs (pull requests)
- Si estás en `develop` y vas a empezar cambios:
  - Crea una rama `feature/*` primero. No commits directos en `develop`.
- Si estás en una `feature/*` y vas a abrir un PR:
  - Base del PR: `pre-release` (evitar `main`).
  - Título descriptivo y cuerpo con: cambios, pruebas, cobertura, migraciones, breaking changes.
- Si estás en `develop` y hubo cambios en `pre-release`:
  - Trae esos cambios (merge `origin/pre-release` -> `develop`).
- Si un PR fue mergeado a `pre-release` y se requiere desplegar/release:
  - Ver sección Releases.

### Checklist mínimo para PRs
- [ ] Ejecuté tests localmente (`python -m pytest -q`) y están verdes.
- [ ] Alternativamente validé con script: Windows `./scripts/setup.ps1 -Test` o Linux/macOS `./scripts/setup.sh --test`.
- [ ] Mensajes de commit siguiendo Conventional Commits (feat, fix, chore, docs, etc.).
- [ ] Incluí migraciones de Django si cambié modelos (`src/core_auth/migrations/*`).
- [ ] Verifiqué que `settings.py` y variables `.env` nuevas están documentadas (ej.: `WHATSAPP_CONTACT`, `PASSWORD_RESET_TICKET_TTL_HOURS`, `TEMP_PASSWORD_LENGTH`).
- [ ] Actualicé templates y admin si cambié campos visibles.
- [ ] Describí el flujo de verificación manual y consideraciones de seguridad si aplica.
- [ ] No hay cambios fuera del alcance (solo `core_auth`/`core_app` salvo documentación).

Pseudocódigo del flujo de PRs
```
if branch == develop:
    create_feature_branch()
elif branch.startswith('feature/'):
    create_pr(base='pre-release')
else:
    # pre-release o main u otras ramas
    follow_release_or_sync_rules()
```

## Sync entre ramas
- Mantener `develop` sincronizado con `pre-release` regularmente:
  - `git checkout develop`
  - `git fetch --all --prune`
  - `git merge --no-ff origin/pre-release -m "Merge pre-release into develop"`
- Evitar merges a `main` desde `feature/*`: nunca directo a producción.

## Releases
- Objetivo: promover cambios probados en `pre-release` a `main`.
- Pasos sugeridos:
  1) Validar CI verde en `pre-release` y aprobación QA.
  2) Crear PR de `pre-release` -> `main` (revisión final).
  3) Al mergear en `main`:
     - Crear tag semántico (ej: `vX.Y.Z`): `git tag -a vX.Y.Z -m "Release vX.Y.Z"` y `git push origin vX.Y.Z`.
     - Opcional: GitHub Release con changelog.
  4) Desplegar desde `main` (pipeline de CD si existe).

## Backport: ¿qué es y cuándo?
- Backport = aplicar cambios ya integrados en una rama más adelantada a otra rama base diferente.
- Ejemplos:
  - Se mergeó una feature en `pre-release`, pero también se necesita en `develop` (si divergieron): merge `pre-release` -> `develop`.
  - Se hizo un hotfix en `main` y hay que llevarlo a `pre-release`/`develop`.
- Reglas:
  - Preferir merges limpios (`--no-ff`) y resolver conflictos con cuidado.
  - Registrar en el PR/commit que es un backport y el enlace al PR original.

## Buenas prácticas
- Commits pequeños y descriptivos; mensajes con contexto.
- Ejecutar tests y coverage localmente antes de push.
- No empujar directamente a `main` ni `pre-release` sin PR.
- Limpiar ramas `feature/*` tras merge (borrar local y remoto).

## Comandos útiles (resumen)
- Crear feature: `git checkout develop && git pull --ff-only && git checkout -b feature/{app}/{desc}`
- Abrir PR a pre-release (con gh): `gh pr create --base pre-release --head feature/{app}/{desc} ...`
- Sync pre-release -> develop: `git checkout develop && git fetch && git merge --no-ff origin/pre-release -m "Merge pre-release into develop"`
- Release: PR `pre-release` -> `main`, luego tag `vX.Y.Z` y push del tag.
