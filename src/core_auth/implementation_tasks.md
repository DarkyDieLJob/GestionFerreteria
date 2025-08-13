# Lista de Tareas Enriquecida: Implementación de core_auth

> Nota de estado: la autenticación básica está implementada y los tests pasan al 100%. Ver `src/core_auth/status.md`. Stack objetivo: Python 3.9+ y Django 4.2 LTS.

## 1. Configuración Inicial

### [ ] 1.1 Configuración de la Aplicación
- **Qué**: Crear/actualizar `apps.py` con la configuración de la aplicación.
- **Por qué**: Para registrar correctamente la aplicación en Django y configurar cualquier parámetro específico.
- **Evitar**: No agregar lógica de negocio aquí, solo configuración.

### [ ] 1.2 Configuración de URLs
- **Qué**: Configurar `urls.py` en el directorio de la aplicación.
- **Por qué**: Para definir los endpoints de autenticación (login, registro, logout).
- **Evitar**: No implementar la lógica aquí, solo el enrutamiento a las vistas.

## 2. Dominio (Domain Layer)

### [ ] 2.1 Definir Interfaces de Puerto
- **Qué**: Crear `ports/interfaces.py` con las interfaces para el repositorio de autenticación.
- **Por qué**: Para definir el contrato que deben seguir los adaptadores.
- **Evitar**: No implementar lógica aquí, solo las firmas de los métodos.

### [ ] 2.2 Implementar Casos de Uso
- **Qué**: Crear `domain/use_cases.py` con las clases `RegisterUserUseCase`, `LoginUserUseCase`, `LogoutUserUseCase`.
- **Por qué**: Para encapsular la lógica de negocio de autenticación.
- **Evitar**: No interactuar directamente con Django, solo con las interfaces definidas.

## 3. Adaptadores (Adapters Layer)

### [ ] 3.1 Implementar Repositorio
- **Qué**: Crear `adapters/repository.py` que implemente las interfaces del puerto.
- **Por qué**: Para manejar la persistencia de datos usando los modelos de Django.
- **Evitar**: No incluir lógica de negocio, solo operaciones CRUD.

### [ ] 3.2 Crear Formularios
- **Qué**: Implementar `adapters/forms.py` con los formularios de registro y login.
- **Por qué**: Para validar los datos de entrada del usuario.
- **Evitar**: No incluir estilos aquí, solo validaciones de datos.

### [ ] 3.3 Implementar Vistas
- **Qué**: Crear `adapters/views.py` con las vistas basadas en clases.
- **Por qué**: Para manejar las solicitudes HTTP y orquestar los casos de uso.
- **Evitar**: Mantener la lógica de negocio en los casos de uso, no en las vistas.

## 4. Interfaz de Usuario

### [ ] 4.1 Plantilla Base
- **Qué**: Crear `templates/auth/base.html` con la estructura común.
- **Por qué**: Para mantener consistencia en todas las páginas de autenticación.
- **Evitar**: No incluir lógica de negocio, solo la estructura HTML y estilos.

### [ ] 4.2 Plantilla de Registro
- **Qué**: Implementar `templates/auth/register.html` con el formulario de registro.
- **Por qué**: Para permitir a los usuarios crear una nueva cuenta.
- **Evitar**: No incluir lógica de JavaScript compleja, solo el formulario y mensajes de error.

### [ ] 4.3 Plantilla de Login
- **Qué**: Implementar `templates/auth/login.html` con el formulario de inicio de sesión.
- **Por qué**: Para permitir a los usuarios autenticarse.
- **Evitar**: No incluir lógica de autenticación, solo la presentación.

### [ ] 4.4 Plantilla de Logout
- **Qué**: Crear `templates/auth/logout.html` con la confirmación de cierre de sesión.
- **Por qué**: Para proporcionar retroalimentación al usuario.
- **Evitar**: No incluir lógica de negocio, solo la confirmación visual.

## 5. Pruebas

### [ ] 5.1 Pruebas de Unidad para Casos de Uso
- **Qué**: Crear `tests/test_use_cases.py` con pruebas para cada caso de uso.
- **Por qué**: Para asegurar que la lógica de negocio funcione correctamente.
- **Evitar**: No probar la implementación, solo el comportamiento esperado.

### [ ] 5.2 Pruebas para Adaptadores
- **Qué**: Implementar `tests/test_adapters.py` con pruebas para el repositorio y vistas.
- **Por qué**: Para verificar que los adaptadores funcionan según lo esperado.
- **Evitar**: No probar la implementación interna de Django, solo la integración.

## 6. Integración

### [ ] 6.1 Configuración de URLs Principales
- **Qué**: Asegurar que las URLs de autenticación estén incluidas en las URLs principales del proyecto.
- **Por qué**: Para que los usuarios puedan acceder a las páginas de autenticación.
- **Evitar**: No duplicar la configuración de URLs.

### [ ] 6.2 Configuración de Autenticación
- **Qué**: Verificar la configuración en `settings.py` para autenticación.
- **Por qué**: Para asegurar que Django use el backend de autenticación correcto.
- **Evitar**: No modificar configuraciones que no sean necesarias.

## 7. Documentación

### [ ] 7.1 Documentar el Código
- **Qué**: Agregar docstrings a todas las clases y métodos importantes.
- **Por qué**: Para facilitar el mantenimiento y la colaboración.
- **Evitar**: No documentar lo obvio, solo lo que no sea autoexplicativo.

### [ ] 7.2 Actualizar README
- **Qué**: Actualizar la documentación del módulo en el README del proyecto.
- **Por qué**: Para que otros desarrolladores entiendan cómo funciona la autenticación.
- **Evitar**: No incluir información desactualizada o incorrecta.

## 8. Revisión Final

### [ ] 8.1 Revisión de Código
- **Qué**: Revisar todo el código implementado.
- **Por qué**: Para asegurar la calidad y consistencia.
- **Evitar**: No dejar pasar problemas de seguridad o rendimiento.

### [ ] 8.2 Pruebas de Integración
- **Qué**: Probar el flujo completo de autenticación.
- **Por qué**: Para asegurar que todos los componentes funcionan juntos correctamente.
- **Evitar**: No asumir que si las pruebas unitarias pasan, todo está bien.

## Consideraciones Adicionales

- **Seguridad**: Asegurar que todas las contraseñas se almacenen de forma segura.
- **Rendimiento**: Optimizar las consultas a la base de datos.
- **Experiencia de Usuario**: Proporcionar mensajes de error claros y útiles.
- **Accesibilidad**: Asegurar que las páginas sean accesibles.

## Priorización

1. Configuración inicial y casos de uso básicos (login, registro, logout).
2. Interfaces de usuario básicas.
3. Pruebas unitarias.
4. Mejoras en la experiencia de usuario.
5. Documentación y revisión final.
