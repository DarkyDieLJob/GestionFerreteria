# Objetivos para Implementar ADR-0002: GitHub Template Repository

> Nota: Esta guía actualizada reemplaza la versión histórica de creación "desde cero" y se enfoca en una checklist secuencial para completar la adopción de GitHub Template Repository en "DjangoProyects". El flujo recomendado sigue siendo clonar el repo y usar scripts de setup, pero ahora incorpora la generación de proyectos derivados y sincronización.

## Flujo Rápido (Clonación + Scripts + Template)

- Clona el repo y entra a la carpeta raíz del proyecto.
- Windows (PowerShell):
  ```powershell
  scripts/setup.ps1 -Requirements notebook -ActivateShell -Test -RunServer
  ```
- Linux/macOS (bash):
  ```bash
  bash scripts/setup.sh --requirements notebook --test
  ```
- Variables de entorno: copia `src/.env.example` a `src/.env` y ajusta valores.
- Crear superusuario (desde `src/` con venv activo):
  ```powershell
  python manage.py createsuperuser
  ```
- Consulta `README.md` para más detalles de opciones (`dev`, `notebook`, integración de frontend con Tailwind, etc.).
- Una vez completada la checklist a continuación, usa el template para generar derivados como "Ferreteria_v4" o "TeatroBar_v2".

Este documento detalla una checklist secuencial para completar ADR-0002. Cada ítem incluye una descripción breve, acciones requeridas y criterios de verificación. La implementación se considera completa cuando todos los checks estén marcados como [x], con evidencia (p.ej., capturas de GitHub, commits o pruebas locales).

## Checklist Secuencial para Completar ADR-0002

1. **Configurar el Repositorio como Template en GitHub**  
   - **Descripción**: Marcar "DjangoProyects" como template para habilitar la generación de nuevos repos.  
   - **Acciones**: En GitHub > Settings > General, activar "Template repository".  
   - **Verificación**: [ ] Confirmar que aparece el botón "Use this template" en la página principal del repo. **Evidencia**: Captura de pantalla o enlace al repo.

2. **Verificar Archivos Clave para Nuevos Clones**  
   - **Descripción**: Asegurar que el template incluya archivos esenciales para setups iniciales en derivados.  
   - **Acciones**: Revisar y actualizar si necesario `.gitignore` (ignorar `.env`, `venv/`, `data/*.sqlite3`), `.env.example` (con placeholders como `SECRET_KEY=changeme`), y scripts (`setup.sh`, `setup.ps1`) para compatibilidad multiplataforma.  
   - **Verificación**: [ ] Ejecutar scripts localmente en un clon fresco y confirmar que crean venv, instalan deps, preparan `.env` y migran DB sin errores. **Evidencia**: Log de ejecución exitosa.

3. **Crear un Proyecto Derivado de Prueba**  
   - **Descripción**: Generar un repo derivado para validar el template.  
   - **Acciones**: Usar "Use this template" en GitHub para crear un repo de prueba (p.ej., "ProyectoDerivadoTest"). Clonar localmente, personalizar (p.ej., cambiar `PROJECT_NAME` en `settings.py` si aplica), y ejecutar setup scripts.  
   - **Verificación**: [ ] El derivado se inicia correctamente (migrate, runserver) y mantiene la estructura hexagonal. **Evidencia**: Acceso a http://127.0.0.1:8000/ en el derivado.

4. **Demostrar Sincronización Base → Derivado**  
   - **Descripción**: Probar la propagación de cambios del base a un derivado.  
   - **Acciones**: En el base, hacer un cambio simple (p.ej., agregar un comentario en `core_utils/helpers.py`). Commit y push a `main`. En el derivado, agregar remote: `git remote add base https://github.com/tu-usuario/DjangoProyects.git`, fetch, y merge: `git fetch base && git merge base/main`.  
   - **Verificación**: [ ] El cambio aparece en el derivado sin conflictos mayores; tests pasan (`pytest -q`). **Evidencia**: `git log` mostrando el merge.

5. **Demostrar Sincronización Derivado → Base**  
   - **Descripción**: Probar la incorporación de mejoras de un derivado al base (p.ej., simular templates de calendarios en `core_utils`).  
   - **Acciones**: En el derivado de prueba, hacer un cambio reusable (p.ej., agregar un placeholder para templates en `core_utils`). Commit y push. Crear un PR desde el derivado al base en GitHub, or cherry-pick: En el base, `git remote add derivado <url>`, fetch, y `git cherry-pick <commit-hash>`.  
   - **Verificación**: [ ] El cambio se integra al base; CI pasa (tests en GitHub Actions). **Evidencia**: PR mergeado o commit en el base.

6. **Implementar Automatización Parcial en Scripts**  
   - **Descripción**: Extender scripts para facilitar sincronización en derivados.  
   - **Acciones**: Modificar `scripts/setup.sh` y `setup.ps1` para agregar un paso opcional que configure el remote del base (p.ej., con flag `--sync-base <url>` que ejecute `git remote add base <url> && git fetch base`).  
   - **Verificación**: [ ] Ejecutar script con flag en un derivado y confirmar que el remote se agrega correctamente. **Evidencia**: `git remote -v` mostrando "base".

7. **Actualizar Documentación**  
   - **Descripción**: Documentar el nuevo flujo en archivos clave.  
   - **Acciones**: Actualizar `README.md` con sección "Usar como Template" (instrucciones para generar derivados y sincronizar). Actualizar `docs/INSTALACION.md` con pasos para sync (p.ej., "Para sincronizar con el base: `git remote add base <url> && git fetch base && git merge base/main`").  
   - **Verificación**: [ ] Documentos reflejan el flujo; links a ADR-0002. **Evidencia**: Commit con actualizaciones.

8. **Validar Flujo Completo y Cleanup**  
   - **Descripción**: Probar end-to-end y limpiar recursos de prueba.  
   - **Acciones**: Generar un segundo derivado, sincronizar cambios bidireccionales, y ejecutar tests/migrate en todos. Borrar repo de prueba si no se necesita.  
   - **Verificación**: [ ] Todo funciona sin issues; ADR-0002 marcado como completado en logs o changelog. **Evidencia**: Resumen de pruebas exitosas.

## Notas para Clonación y Derivados
- Clonar el repositorio base o derivado.
- Copiar `.env.example` a `.env` y configurar variables.
- Instalar dependencias (`pip install -r requirements/notebook.txt`).
- Ejecutar migraciones: `python manage.py migrate --database=default` (y por app si aplica).
- Crear nuevas aplicaciones: `cd src && python ../manage.py startapp <nombre> --template=../templates/app_template`.
- Actualizar `INSTALLED_APPS` y `database_routers.py` para nuevas apps en derivados.
- Para sincronización avanzada, considera backports como se describe en `GIT_AGENTES.md`.

## Tiempo Total Estimado
- Aproximadamente **1-2 horas** para la checklist inicial, asumiendo familiaridad con GitHub y Git.

## Prioridades
- Completar checks en orden secuencial para evitar dependencias rotas.
- Enfocarse en sincronización bidireccional para reusability (p.ej., apps como `core_utils`).
- Documentar cada paso para facilitar la extensión y mantenimiento del template.