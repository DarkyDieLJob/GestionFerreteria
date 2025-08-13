# ADR-0001: Adopción de la Arquitectura Hexagonal para el Proyecto Base

## Estado
Aceptado

## Fecha
2025-08-04

## Contexto
Como base para nuevos proyectos en Django, necesitamos una arquitectura que garantice modularidad, testabilidad y separación de preocupaciones, siendo viable para un desarrollador solo. La arquitectura debe soportar inicio de sesión con y sin redes sociales, endpoints REST con autenticación por tokens, y permitir que cada aplicación defina su propia base de datos para evitar bloqueos entre operaciones (ej. actualizaciones masivas de artículos vs. escritura en el carrito). Además, se requiere una forma de crear nuevas aplicaciones con una estructura hexagonal predefinida.

## Decisión
Adoptamos una **arquitectura hexagonal** (Ports and Adapters) como base para todos los proyectos, estructurada en:
- **Dominio**: Casos de uso (`domain/use_cases.py`) que encapsulan la lógica de negocio.
- **Puertos**: Interfaces (`ports/interfaces.py`) que definen contratos para interactuar con el exterior.
- **Adaptadores**: Implementaciones específicas (`adapters/models.py`, `adapters/views.py`, `adapters/serializers.py`, `adapters/repository.py`, `adapters/urls.py`) para la base de datos, UI, y API REST.

Esta arquitectura se implementará en Django con aplicaciones modulares (`core_app`, `core_auth`, `api`, etc.) y soportará:
- Autenticación local y social usando `django-allauth`.
- Endpoints REST opcionales con Django REST Framework (DRF) y autenticación por tokens.
- Múltiples bases de datos:
  - `default`: Para aplicaciones sin base de datos específica.
  - `core_app_db`: Para datos de artículos, conectada a `core_app`.
  - Nuevas aplicaciones pueden definir su base de datos en `config.py`.
- Creación automatizada de aplicaciones con una plantilla personalizada (`templates/app_template/`) para `startapp`.
- Pruebas estructuradas por casos de uso y adaptadores.

Los endpoints REST se limitarán a casos específicos para evitar complejidad innecesaria.

## Consecuencias
### Positivas
- Modularidad: La lógica de negocio está aislada, facilitando cambios.
- Testabilidad: Los casos de uso son fáciles de probar de forma aislada.
- Reusabilidad: Los puertos permiten cambiar adaptadores (ej. bases de datos) sin afectar el dominio.
- Consistencia: Estructura común para todos los proyectos, facilitando la clonación.
- Evita bloqueos: Múltiples bases de datos permiten operaciones independientes por aplicación.
- Automatización: La plantilla `startapp` asegura que nuevas aplicaciones sigan la estructura hexagonal.

### Negativas
- Complejidad inicial: Configurar puertos, adaptadores, múltiples bases de datos y plantillas requiere más esfuerzo.
- Curva de aprendizaje: Puede ser desafiante para desarrolladores nuevos en hexagonal.
- Configuración centralizada: Aunque las aplicaciones definen sus bases de datos en `config.py`, `settings.py` y el router deben actualizarse.

## Alternativas Consideradas
1. **Arquitectura en Capas**:
   - **Ventajas**: Más simple, ideal para desarrolladores solos, rápida de implementar.
   - **Desventajas**: Menos modularidad, menos flexible para múltiples bases de datos.
2. **Arquitectura Monolítica Simple**:
   - **Ventajas**: Muy rápida de implementar.
   - **Desventajas**: Difícil de mantener, propensa a bloqueos en una sola base de datos.
3. **Microservicios**:
   - **Ventajas**: Alta escalabilidad, independencia de componentes.
   - **Desventajas**: Muy complejo para un desarrollador solo, alto costo de mantenimiento.

La arquitectura hexagonal se eligió por su modularidad, testabilidad y capacidad para manejar múltiples bases de datos, con una plantilla personalizada para simplificar la creación de aplicaciones.

## Referencias
- [Documentación de Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Allauth](https://django-allauth.readthedocs.io/)
- [Arquitectura Hexagonal](https://alistair.cockburn.us/hexagonal-architecture/)
- [Múltiples Bases de Datos en Django](https://docs.djangoproject.com/en/stable/topics/db/multi-db/)
- [Personalizar startapp](https://docs.djangoproject.com/en/stable/ref/django-admin/#startapp)