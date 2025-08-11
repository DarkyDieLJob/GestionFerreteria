# ADR-0002: Adopción de GitHub Template Repository para DjangoProyects como Esqueleto Base

## Estado
Aceptado

## Fecha
2025-08-10

## Contexto
El proyecto "DjangoProyects" (v1.2.1) está diseñado como un esqueleto o base reusable para crear nuevos proyectos Django, como "Ferreteria_v4" (buscador de artículos, carrito) y "TeatroBar_v2" (eventos, calendarios). La meta es permitir la creación rápida de proyectos derivados mientras se facilita la sincronización de mejoras entre el esqueleto base y los derivados, o entre derivados (p.ej., mover templates de calendarios desde TeatroBar_v2 a `core_utils` para uso en Ferreteria_v4). Copiar y renombrar el repositorio manualmente genera duplicación de código y dificulta la sincronización. Necesitamos un enfoque simple, compatible con el flujo Git existente (ver `GIT_AGENTES.md`), que funcione para un desarrollador solo y no requiera herramientas externas complejas.

## Decisión
Convertiremos "DjangoProyects" en un **GitHub Template Repository** para usarlo como base para generar nuevos proyectos. Los proyectos derivados (p.ej., Ferreteria_v4, TeatroBar_v2) se crearán usando la funcionalidad "Use this template" de GitHub. Para sincronizar cambios:
- **Del base a derivados**: Usar `git remote add` y `git merge` (o `git cherry-pick` para cambios específicos) desde el base hacia los derivados.
- **De derivados al base**: Crear pull requests (PRs) o cherry-pick commits desde los derivados al base para incorporar mejoras (p.ej., templates de calendarios en `core_utils`).
- Los scripts existentes (`scripts/setup.sh`, `scripts/setup.ps1`) y la estructura hexagonal se mantendrán intactos para facilitar la configuración inicial de los derivados.

## Consecuencias
### Positivas
- **Simplicidad**: Generar nuevos proyectos con un clic en GitHub, sin copias manuales.
- **Compatibilidad**: Integra con el flujo Git actual (`develop`, `pre-release`, `main`, Conventional Commits).
- **Flexibilidad**: Permite sincronizar selectivamente (merge/cherry-pick) cambios generales (base → derivados) o específicos (derivado → base).
- **Mantenimiento ligero**: Ideal para un desarrollador solo, sin herramientas adicionales.
- **Reusabilidad**: Mejoras en apps comunes (p.ej., `core_utils`) pueden backportearse al base para futuros proyectos.

### Negativas
- **Sincronización manual**: Requiere merges o cherry-picks para propagar cambios, lo que puede generar conflictos en archivos como `settings.py` o `urls.py`.
- **Gestión de repos**: Múltiples repos separados (uno por proyecto) aumentan la sobrecarga administrativa frente a un monorepo.
- **Dependencias no paquetizadas**: Apps comunes como `core_utils` no son instalables via pip, lo que implica copiar código o mergear manualmente.

## Alternativas Consideradas
1. **Paquetizar Apps Reusables**:
   - **Ventajas**: Código común (p.ej., `core_utils`) como paquetes pip evita duplicación; fácil actualización con `pip install -U`.
   - **Desventajas**: Requiere refactor para empaquetar apps, más tiempo inicial, no sincroniza configs no-app (p.ej., `settings.py`).
   - **Razón para descartar**: Mayor complejidad inicial; se considerará si los repos crecen significativamente (estimado: 2 días de trabajo).
2. **Monorepo con Subdirectorios**:
   - **Ventajas**: Cambios en apps comunes se aplican instantáneamente; un solo repo.
   - **Desventajas**: Repo grande, despliegues más complejos, menos "esqueleto" puro.
   - **Razón para descartar**: Menos flexible para proyectos independientes; no escalaría bien con muchos derivados.
3. **Cookiecutter Template**:
   - **Ventajas**: Automatiza generación con placeholders; ideal para múltiples proyectos.
   - **Desventajas**: Curva de aprendizaje, requiere reestructurar archivos con placeholders.
   - **Razón para descartar**: Overhead innecesario para pocos proyectos; considerado para futuro si se necesitan más automatizaciones.

## Implementación
1. **Configurar Template Repository**:
   - En GitHub, en "DjangoProyects" > Settings > General, marcar "Template repository".
   - Verificar que `.gitignore`, `.env.example`, y scripts (`setup.sh`, `setup.ps1`) estén completos para nuevos clones.
2. **Crear Proyectos Derivados**:
   - Usar "Use this template" para crear repos como "Ferreteria_v4" o "TeatroBar_v2".
   - Clonar localmente, personalizar (p.ej., `INSTALLED_APPS`, `.env`), y agregar apps específicas.
3. **Sincronizar Cambios**:
   - **Base → Derivado**: En el derivado, agregar remote: `git remote add base https://github.com/tu-usuario/DjangoProyects.git`, luego `git fetch base` y `git merge base/main` (o `git cherry-pick <commit>` para cambios específicos).
   - **Derivado → Base**: Crear PR desde el derivado al base (o cherry-pick commits). Ejemplo: mover templates de calendarios de TeatroBar_v2 a `core_utils` en el base.
   - Resolver conflictos en archivos sensibles (p.ej., `settings.py`, `urls.py`).
4. **Automatización Parcial**:
   - Extender `scripts/setup.sh` para incluir un paso que configure el remote del base y facilite merges.
   - Ejemplo: Agregar `git remote add base <url> && git fetch base` en el script.
5. **Documentación**:
   - Actualizar `README.md` y `docs/INSTALACION.md` con instrucciones para usar el template y sincronizar.
   - Ejemplo: "Para sincronizar con el base: `git remote add base <url> && git fetch base && git merge base/main`".

## Referencias
- [GitHub Template Repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository)
- [DjangoProyects README.md](README.md)
- [Flujo Git (GIT_AGENTES.md)](docs/GIT_AGENTES.md)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Merge y Cherry-pick](https://git-scm.com/docs/git-merge)
- [Arquitectura Hexagonal (ADR-0001)](docs/adr/0001-adopcion-arquitectura-hexagonal.md)