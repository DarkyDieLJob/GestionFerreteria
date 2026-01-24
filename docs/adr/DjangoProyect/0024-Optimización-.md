Architecture Decision Record (ADR0023): Optimización de Readiness y Smoke Tests en Flujos CI/CD para Proyectos Heredados

## Estado
Propuesto (Pendiente de revisión final antes de implementación en el repositorio padre y adaptación en proyectos hijos).

## Contexto
En el pipeline CI/CD actual, las etapas de staging incluyen loops de espera para verificar la readiness de servicios como la aplicación principal, utilizando comandos en contenedor para probar respuestas HTTP. Esto permite resiliencia ante latencias transitorias, pero genera falsos positivos cuando fallos intermedios (como timeouts o conexiones rechazadas) se "saltan" gracias a retries, permitiendo que el flujo avance sin resolver causas raíz. Además, warnings sobre variables de entorno no seteadas (como credenciales de base de datos) indican configuraciones incompletas que ralentizan inicializaciones y complican iteraciones rápidas en pruebas con tags.

El enfoque heredado del repositorio padre enfatiza workflows reutilizables con perfiles de servicios y comandos condicionales, pero carece de defaults robustos para manejar estas situaciones en hijos, lo que resulta en setups y builds prolongados durante iteraciones frecuentes. El objetivo es estandarizar un mecanismo más determinístico que minimice tiempos de setup/build (priorizando updates incrementales), provea flags por defecto para tolerancia vs. estrictitud, y facilite adaptaciones en hijos sin romper consistencia.

## Decisión
Adoptar un enfoque híbrido de readiness basado en healthchecks nativos de contenedores, complementado con loops condicionales en workflows, para asegurar verificaciones determinísticas y configurables. Se implementarán defaults en el padre que favorezcan eficiencia en iteraciones (ej. timeouts reducidos y modos tolerantes), con flags para overrides en hijos que permitan manejar situaciones específicas (ej. entornos con latencia variable o debugging estricto). Esto integra directamente al pipeline CI/CD, minimizando rebuilds innecesarios mediante caching heredado y condicionales de cambio.

## Pasos a Seguir para la Implementación
1. **Estandarizar healthchecks nativos en el padre**:
   - Definir healthchecks por defecto para servicios clave (base de datos, broker y aplicación), utilizando comandos livianos que verifiquen conexiones y estados operativos.
   - Configurar dependencias condicionales para que los servicios esperen automáticamente antes de marcarse como ready, reduciendo la necesidad de loops manuales en workflows.

2. **Parametrizar loops de readiness y smoke tests**:
   - Incluir flags por defecto en workflows reutilizables (ej. SMOKE_TIMEOUT=60 para iteraciones rápidas, SMOKE_MODE=tolerant para staging), con opciones para strict (abort en fallos intermedios) o verbose (logging detallado).
   - Manejar situaciones como variables no seteadas mediante validaciones previas, con defaults seguros o fallbacks que eviten warnings y ralentizaciones.

3. **Minimizar setup y build en iteraciones**:
   - Integrar condicionales para builds incrementales (ej. skip si no hay cambios en dependencias o código core), priorizando pulls de artefactos existentes en lugar de rebuilds completos.
   - En etapas de staging, reutilizar estados persistentes para evitar setups repetitivos, con flags para "fast-iter" que reduzcan timeouts y toleren transitorios sin reconstrucción.

4. **Herencia y adaptaciones en hijos**:
   - Proveer documentación en el padre sobre puntos de override (ej. ajuste de flags vía inputs de workflow o archivos de entorno), asegurando que hijos mantengan mínimas personalizaciones.
   - Validar el enfoque en entornos heterogéneos, priorizando eficiencia en pruebas con tags.

5. **Monitoreo y refinamiento**:
   - Incluir métricas básicas para tiempos de readiness y build, permitiendo iteraciones futuras basadas en ejecuciones reales.

## Alternativas Consideradas
- Loops manuales extendidos: Más simples inicialmente, pero menos determinísticos y propensos a falsos positivos, descartado por no minimizar iteraciones.
- Healthchecks estrictos sin flags: Aumenta robustez, pero reduce flexibilidad en hijos con latencias variables, descartado por herencia rígida.
- Builds siempre completos: Garantiza consistencia, pero agrava tediosidad en pruebas, descartado en favor de incrementales.

## Consecuencias
- Positivas: Mayor eficiencia en iteraciones, reducción de falsos positivos en staging, y adaptabilidad heredada para hijos.
- Negativas: Complejidad inicial en configuración de flags; posible overhead en validaciones si no se calibran bien.
- Neutrales: Requiere pruebas periódicas para entornos variables, escalable hacia automatización completa de setups.